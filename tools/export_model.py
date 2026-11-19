"""Export the supplied sklearn forest to a data-only JSON runtime asset.

The loader permits only the model, numpy, and joblib classes found in the
checked-in heart_disease_rf_model.pkl artifact. Do not broaden this allowlist
for arbitrary pickle files.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib.numpy_pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier


class ModelOnlyUnpickler(joblib.numpy_pickle.NumpyUnpickler):
    ALLOWED = {
        ("sklearn.ensemble._forest", "RandomForestClassifier"),
        ("sklearn.tree._classes", "DecisionTreeClassifier"),
        ("sklearn.tree._tree", "Tree"),
        ("joblib.numpy_pickle", "NumpyArrayWrapper"),
        ("numpy", "ndarray"),
        ("numpy", "dtype"),
        ("numpy._core.multiarray", "_reconstruct"),
        ("numpy._core.multiarray", "scalar"),
    }

    def find_class(self, module: str, name: str):
        if (module, name) not in self.ALLOWED:
            raise ValueError(f"Unexpected pickle global: {module}.{name}")
        return super().find_class(module, name)


def load_model(path: Path) -> RandomForestClassifier:
    with path.open("rb") as source:
        model = ModelOnlyUnpickler(str(path), source, True).load()
    if not isinstance(model, RandomForestClassifier):
        raise TypeError("Expected a fitted RandomForestClassifier.")
    if not hasattr(model, "feature_names_in_") or not hasattr(model, "estimators_"):
        raise ValueError("Model is missing fitted feature names or trees.")
    return model


def json_number(value):
    value = value.item() if hasattr(value, "item") else value
    if isinstance(value, (int, float, str, bool)) or value is None:
        return value
    raise TypeError(f"Unsupported model value: {type(value)!r}")


def export(model: RandomForestClassifier, destination: Path) -> None:
    features = [str(name) for name in model.feature_names_in_]
    trees = []
    for estimator in model.estimators_:
        tree = estimator.tree_
        leaf_probabilities = []
        for index in range(tree.node_count):
            if tree.children_left[index] == tree.children_right[index]:
                counts = np.asarray(tree.value[index][0], dtype=np.float64)
                total = float(counts.sum())
                if total <= 0:
                    raise ValueError("Encountered a leaf with no class mass.")
                leaf_probabilities.append([float(v / total) for v in counts])
            else:
                leaf_probabilities.append(None)
        trees.append(
            {
                "left": tree.children_left.tolist(),
                "right": tree.children_right.tolist(),
                "feature": tree.feature.tolist(),
                "threshold": [float(v) for v in tree.threshold],
                "leafProbabilities": leaf_probabilities,
            }
        )

    payload = {
        "format": "heart-risk-random-forest-v1",
        "sklearnVersion": str(model.__getstate__().get("_sklearn_version", "unknown")),
        "featureNames": features,
        "classes": [json_number(value) for value in model.classes_],
        "trees": trees,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print(f"Exported {len(trees)} trees, {len(features)} features to {destination}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        type=Path,
        default=Path("heart_disease_rf_model.pkl"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("assets/models/heart_disease_rf_model.json"),
    )
    args = parser.parse_args()
    forest = load_model(args.model)
    print("Feature order:", ", ".join(str(x) for x in forest.feature_names_in_))
    print("Classes:", [json_number(x) for x in forest.classes_])
    export(forest, args.output)
