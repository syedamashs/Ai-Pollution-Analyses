#!/usr/bin/env python3
"""AQI-driven tree recommendation model.

This module trains a simple classifier from a tree species dataset.
Given AQI category (1..5), it ranks tree species by suitability probability.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.model_selection import train_test_split


class TreeRecommendationModel:
    """Train and serve AQI-based tree suitability recommendations."""

    def __init__(
        self,
        dataset_path: str | Path,
        city_profile_path: str | Path = "Data/city_profile_dataset.csv",
        impact_dataset_path: str | Path = "Data/impact_training_dataset.csv",
        feedback_path: str | Path = "Data/recommendation_feedback.jsonl",
    ) -> None:
        self.dataset_path = Path(dataset_path)
        self.city_profile_path = Path(city_profile_path)
        self.impact_dataset_path = Path(impact_dataset_path)
        self.feedback_path = Path(feedback_path)
        self.species_rows: List[Dict[str, Any]] = []
        self.city_profiles: Dict[str, Dict[str, float]] = {}
        self.model = RandomForestClassifier(n_estimators=250, random_state=42)
        self.impact_model = RandomForestRegressor(n_estimators=250, random_state=42)
        self._is_trained = False
        self._impact_is_trained = False

    def load_dataset(self) -> None:
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Tree dataset not found: {self.dataset_path}")

        rows: List[Dict[str, Any]] = []
        with self.dataset_path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "scientific_name": row["scientific_name"],
                        "aqi_min": int(row["aqi_min"]),
                        "aqi_max": int(row["aqi_max"]),
                        "pollution_tolerance": int(row["pollution_tolerance"]),
                        "water_need": int(row["water_need"]),
                        "growth_rate": int(row["growth_rate"]),
                        "maintenance": int(row["maintenance"]),
                        "canopy_score": int(row["canopy_score"]),
                        "native_score": int(row["native_score"]),
                        "benefits": row["benefits"],
                        "reason": row["reason"],
                    }
                )

        self.species_rows = rows

    def load_city_profiles(self) -> None:
        if self.city_profile_path.exists():
            profiles: Dict[str, Dict[str, float]] = {}
            with self.city_profile_path.open("r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    profiles[row["city_id"]] = {
                        "temperature": float(row["temperature"]),
                        "humidity": float(row["humidity"]),
                        "rainfall": float(row["rainfall"]),
                        "urban_density": float(row["urban_density"]),
                    }
            self.city_profiles = profiles
            return

        # Reasonable defaults if profile dataset is not present yet.
        self.city_profiles = {
            "madurai": {"temperature": 31.0, "humidity": 62.0, "rainfall": 85.0, "urban_density": 0.72},
            "chennai": {"temperature": 32.0, "humidity": 74.0, "rainfall": 120.0, "urban_density": 0.91},
            "coimbatore": {"temperature": 28.0, "humidity": 58.0, "rainfall": 75.0, "urban_density": 0.64},
            "dindigul": {"temperature": 29.0, "humidity": 57.0, "rainfall": 65.0, "urban_density": 0.55},
            "trichy": {"temperature": 30.0, "humidity": 60.0, "rainfall": 70.0, "urban_density": 0.68},
        }

    def get_city_profile(self, city_id: str) -> Dict[str, float]:
        if not self.city_profiles:
            self.load_city_profiles()

        return self.city_profiles.get(
            city_id,
            {"temperature": 30.0, "humidity": 60.0, "rainfall": 80.0, "urban_density": 0.65},
        )

    def _feature_vector(self, row: Dict[str, Any], aqi: int, city_profile: Dict[str, float]) -> List[float]:
        return [
            float(aqi),
            float(row["pollution_tolerance"]),
            float(row["water_need"]),
            float(row["growth_rate"]),
            float(row["maintenance"]),
            float(row["canopy_score"]),
            float(row["native_score"]),
            float(city_profile["temperature"]),
            float(city_profile["humidity"]),
            float(city_profile["rainfall"]),
            float(city_profile["urban_density"]),
        ]

    @staticmethod
    def _aqi_fit_score(aqi: int, aqi_min: int, aqi_max: int) -> float:
        if aqi_min <= aqi <= aqi_max:
            return 1.0

        if aqi < aqi_min:
            dist = aqi_min - aqi
        else:
            dist = aqi - aqi_max

        return max(0.0, 1.0 - 0.4 * dist)

    def _build_training_data(self) -> tuple[np.ndarray, np.ndarray]:
        X: List[List[float]] = []
        y: List[int] = []

        if not self.city_profiles:
            self.load_city_profiles()

        for row in self.species_rows:
            for city_profile in self.city_profiles.values():
                for aqi in range(1, 6):
                    in_range = int(row["aqi_min"] <= aqi <= row["aqi_max"])
                    X.append(self._feature_vector(row, aqi, city_profile))
                    y.append(in_range)

                    # Duplicate positives to reduce class imbalance in tiny datasets.
                    if in_range:
                        X.append(X[-1])
                        y.append(in_range)

        return np.array(X, dtype=float), np.array(y, dtype=int)

    def train(self) -> None:
        if not self.species_rows:
            self.load_dataset()
        if not self.city_profiles:
            self.load_city_profiles()

        X, y = self._build_training_data()
        self.model.fit(X, y)
        self._train_impact_model()
        self._is_trained = True

    def _build_impact_training_data(self) -> tuple[np.ndarray, np.ndarray]:
        if not self.impact_dataset_path.exists():
            raise FileNotFoundError(f"Impact dataset not found: {self.impact_dataset_path}")

        X: List[List[float]] = []
        y: List[float] = []
        with self.impact_dataset_path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                X.append(
                    [
                        float(row["aqi"]),
                        float(row["pollution_tolerance"]),
                        float(row["water_need"]),
                        float(row["growth_rate"]),
                        float(row["maintenance"]),
                        float(row["canopy_score"]),
                        float(row["native_score"]),
                        float(row["temperature"]),
                        float(row["humidity"]),
                        float(row["rainfall"]),
                        float(row["urban_density"]),
                        float(row["tree_count"]),
                        float(row["species_mix_ratio"]),
                    ]
                )
                y.append(float(row["pm25_reduction"]))

        return np.array(X, dtype=float), np.array(y, dtype=float)

    def _train_impact_model(self) -> None:
        X_impact, y_impact = self._build_impact_training_data()
        self.impact_model.fit(X_impact, y_impact)
        self._impact_is_trained = True

    def evaluate_impact_model(self) -> Dict[str, Any]:
        X, y = self._build_impact_training_data()
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.3,
            random_state=42,
        )

        eval_model = RandomForestRegressor(n_estimators=250, random_state=42)
        eval_model.fit(X_train, y_train)
        y_pred = eval_model.predict(X_test)

        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        return {
            "r2": round(float(r2_score(y_test, y_pred)), 4),
            "mae": round(float(mean_absolute_error(y_test, y_pred)), 4),
            "rmse": round(rmse, 4),
            "sampleCount": int(len(y)),
            "featureCount": int(X.shape[1]),
            "modelType": "RandomForestRegressor",
        }

    def evaluate(self) -> Dict[str, object]:
        if not self.species_rows:
            self.load_dataset()
        if not self.city_profiles:
            self.load_city_profiles()

        X, y = self._build_training_data()
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.3,
            random_state=42,
            stratify=y,
        )

        eval_model = RandomForestClassifier(n_estimators=250, random_state=42)
        eval_model.fit(X_train, y_train)
        y_pred = eval_model.predict(X_test)

        conf = confusion_matrix(y_test, y_pred, labels=[0, 1]).tolist()
        return {
            "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
            "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
            "confusionMatrix": {
                "labels": ["Not Suitable (0)", "Suitable (1)"],
                "matrix": conf,
            },
            "sampleCount": int(len(y)),
            "featureCount": int(X.shape[1]),
            "modelType": "RandomForestClassifier",
        }

    def _explain_factors(
        self,
        row: Dict[str, Any],
        aqi_value: int,
        city_profile: Dict[str, float],
    ) -> Dict[str, Any]:
        aqi_fit = self._aqi_fit_score(aqi_value, int(row["aqi_min"]), int(row["aqi_max"]))
        pollution_score = float(row["pollution_tolerance"]) / 5.0
        water_fit = max(0.0, 1.0 - abs((float(row["water_need"]) - (city_profile["rainfall"] / 40.0))) / 5.0)
        canopy_score = float(row["canopy_score"]) / 5.0

        factors = [
            {"name": "AQI fit", "score": round(aqi_fit, 3)},
            {"name": "Pollution tolerance", "score": round(pollution_score, 3)},
            {"name": "Water need fit", "score": round(water_fit, 3)},
            {"name": "Canopy score", "score": round(canopy_score, 3)},
        ]
        factors.sort(key=lambda item: item["score"], reverse=True)

        return {
            "aqiFit": round(aqi_fit, 3),
            "pollutionTolerance": int(row["pollution_tolerance"]),
            "waterNeed": int(row["water_need"]),
            "canopyScore": int(row["canopy_score"]),
            "topFactors": factors,
        }

    def _impact_prediction(
        self,
        row: Dict[str, Any],
        aqi_value: int,
        city_profile: Dict[str, float],
        tree_count: int = 100,
        species_mix_ratio: float = 1.0,
    ) -> Dict[str, Any]:
        if not self._impact_is_trained:
            self._train_impact_model()

        features = np.array(
            [
                [
                    float(aqi_value),
                    float(row["pollution_tolerance"]),
                    float(row["water_need"]),
                    float(row["growth_rate"]),
                    float(row["maintenance"]),
                    float(row["canopy_score"]),
                    float(row["native_score"]),
                    float(city_profile["temperature"]),
                    float(city_profile["humidity"]),
                    float(city_profile["rainfall"]),
                    float(city_profile["urban_density"]),
                    float(tree_count),
                    float(species_mix_ratio),
                ]
            ],
            dtype=float,
        )

        pm25_reduction = max(0.0, float(self.impact_model.predict(features)[0]))
        impact_score = min(1.0, pm25_reduction / 6.0)

        return {
            "impactScore": round(float(impact_score), 4),
            "estimatedPm25ReductionPer100Trees": round(pm25_reduction, 4),
            "modelType": "RandomForestRegressor",
        }

    def recommend(self, aqi_value: int, city_id: Optional[str] = None, top_k: int = 6) -> List[Dict[str, Any]]:
        if not self._is_trained:
            self.train()

        city_profile = self.get_city_profile(city_id or "unknown")
        scored: List[Dict[str, Any]] = []

        for row in self.species_rows:
            features = np.array(
                [self._feature_vector(row, int(aqi_value), city_profile)],
                dtype=float,
            )

            suitability = float(self.model.predict_proba(features)[0][1])
            explain = self._explain_factors(row, int(aqi_value), city_profile)
            impact = self._impact_prediction(
                row,
                int(aqi_value),
                city_profile,
                tree_count=100,
                species_mix_ratio=(1.0 / max(1, top_k)),
            )
            scored.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "scientificName": row["scientific_name"],
                    "reason": row["reason"],
                    "pollutionAbsorption": _absorption_label(int(row["pollution_tolerance"])),
                    "benefits": row["benefits"],
                    "modelScore": round(suitability, 4),
                    "modelType": "RandomForestClassifier",
                    "explainability": explain,
                    "impactPrediction": impact,
                }
            )

        scored.sort(key=lambda item: float(item.get("modelScore", 0.0)), reverse=True)
        return scored[:top_k]

    def estimate_mix_impact(
        self,
        city_id: str,
        aqi_value: int,
        tree_count: int,
        species_mix: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        city_profile = self.get_city_profile(city_id)
        id_to_row: Dict[str, Dict[str, Any]] = {str(row["id"]): row for row in self.species_rows}

        total_pm25_reduction = 0.0
        details: List[Dict[str, Any]] = []
        valid_mix = [item for item in species_mix if str(item.get("treeId", "")) in id_to_row]

        if not valid_mix:
            return {
                "cityId": city_id,
                "aqi": int(aqi_value),
                "treeCount": int(tree_count),
                "estimatedTotalPm25Reduction": 0.0,
                "mixImpactScore": 0.0,
                "speciesBreakdown": [],
            }

        ratio_sum = sum(float(item.get("ratio", 0.0)) for item in valid_mix)
        if ratio_sum <= 0:
            ratio_sum = 1.0

        for item in valid_mix:
            tree_id = str(item.get("treeId"))
            ratio = float(item.get("ratio", 0.0)) / ratio_sum
            row = id_to_row[tree_id]

            prediction = self._impact_prediction(
                row,
                int(aqi_value),
                city_profile,
                tree_count=int(tree_count),
                species_mix_ratio=ratio,
            )
            contribution = float(prediction["estimatedPm25ReductionPer100Trees"])
            total_pm25_reduction += contribution

            details.append(
                {
                    "treeId": tree_id,
                    "name": row["name"],
                    "ratio": round(ratio, 4),
                    "predictedPm25Reduction": round(contribution, 4),
                    "impactScore": prediction["impactScore"],
                }
            )

        mix_score = min(1.0, total_pm25_reduction / 8.0)
        return {
            "cityId": city_id,
            "aqi": int(aqi_value),
            "treeCount": int(tree_count),
            "estimatedTotalPm25Reduction": round(total_pm25_reduction, 4),
            "mixImpactScore": round(mix_score, 4),
            "speciesBreakdown": details,
            "modelType": "RandomForestRegressor",
        }

    def simulate_scenario(self, city_id: str, current_aqi: int, target_aqi: int) -> Dict[str, object]:
        target = max(1, min(5, int(target_aqi)))
        current = max(1, min(5, int(current_aqi)))
        improvement_needed = max(0, current - target)

        top_mix = self.recommend(current, city_id=city_id, top_k=3)
        if not top_mix:
            return {
                "currentAQI": current,
                "targetAQI": target,
                "improvementSteps": improvement_needed,
                "speciesMix": [],
                "estimatedTotalTrees": 0,
            }

        # 1 AQI-category drop is represented as 300 trees baseline in this prototype.
        total_trees = improvement_needed * 300
        mix_alloc = [0.4, 0.35, 0.25]

        species_mix = []
        for i, item in enumerate(top_mix):
            count = int(round(total_trees * mix_alloc[i])) if improvement_needed > 0 else 0
            species_mix.append(
                {
                    "name": item["name"],
                    "recommendedCount": count,
                    "impactScore": item.get("impactPrediction", {}).get("impactScore", 0),
                }
            )

        return {
            "currentAQI": current,
            "targetAQI": target,
            "improvementSteps": improvement_needed,
            "speciesMix": species_mix,
            "estimatedTotalTrees": int(sum(item["recommendedCount"] for item in species_mix)),
        }

    def store_feedback(
        self,
        city_id: str,
        aqi_value: int,
        shown_tree_ids: List[str],
        selected_tree_ids: List[str],
        note: str = "",
    ) -> Dict[str, object]:
        self.feedback_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "city_id": city_id,
            "aqi": int(aqi_value),
            "shown_tree_ids": shown_tree_ids,
            "selected_tree_ids": selected_tree_ids,
            "note": note,
        }

        with self.feedback_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")

        return {
            "status": "saved",
            "feedbackPath": str(self.feedback_path),
            "savedAt": payload["timestamp"],
        }


def _absorption_label(tolerance: int) -> str:
    if tolerance >= 5:
        return "Very High"
    if tolerance == 4:
        return "High"
    if tolerance == 3:
        return "Medium"
    return "Low"


_MODEL_SINGLETON: TreeRecommendationModel | None = None


def get_tree_recommendation_model() -> TreeRecommendationModel:
    global _MODEL_SINGLETON
    if _MODEL_SINGLETON is None:
        _MODEL_SINGLETON = TreeRecommendationModel("Data/tree_species_dataset.csv")
        _MODEL_SINGLETON.train()
    return _MODEL_SINGLETON
