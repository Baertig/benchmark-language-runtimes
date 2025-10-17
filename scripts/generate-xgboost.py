import xgboost as xgb
import numpy as np
from sklearn.datasets import load_digits

# --- Model Parameters (Tweak these to change model size) ---
# Your original model has NUM_TREES = 40. Let's reduce it.
NEW_NUM_TREES = 5
# Your original model has deep trees. Let's limit the depth.
NEW_MAX_DEPTH = 4


def format_c_array(name, data, data_type="uint8_t"):
    """Formats a Python list into a C-style array string."""
    c_code = f"const {data_type} {name}[] = {{"
    for val in data:
        c_code += f"{val},"

    c_code += "};"
    return c_code


def export_model_to_c_format(model):
    """
    Parses a trained XGBoost model and extracts data into lists
    matching the C file's structure.
    """
    print(
        f"// Exporting model with {NEW_NUM_TREES} trees/class and max_depth={NEW_MAX_DEPTH}\n"
    )

    # XGBoost's internal representation of the model
    df = model.get_booster().trees_to_dataframe()

    all_tree_sizes = []
    all_comparison_idxs = []
    all_comparison_values = []
    all_left_children = []
    all_right_children = []
    all_leaf_values = []

    num_classes = model.n_classes_

    for class_id in range(num_classes):
        for tree_id in range(NEW_NUM_TREES):
            # XGBoost tree ID is class_id * num_trees + tree_id
            xgb_tree_index = class_id * NEW_NUM_TREES + tree_id

            tree_df = df[df["Tree"] == xgb_tree_index].copy()

            # Separate nodes and leaves
            nodes = tree_df[tree_df["Feature"] != "Leaf"].sort_values("Node")
            leaves = tree_df[tree_df["Feature"] == "Leaf"]

            # --- Create mappings from XGBoost IDs to simple 0-indexed IDs ---
            node_map = {node_id: i for i, node_id in enumerate(nodes["ID"])}
            leaf_map = {}

            # In the C code, leaves have MSB set. Index is the lower 7 bits.
            leaf_counter = 0
            for leaf_id in leaves["ID"]:
                leaf_map[leaf_id] = 0x80 | leaf_counter
                leaf_counter += 1

            # --- Populate the arrays for this specific tree ---
            tree_size = len(nodes)
            all_tree_sizes.append(tree_size)

            tree_comp_idxs = [0] * tree_size
            tree_comp_values = [0] * tree_size
            tree_left = [0] * tree_size
            tree_right = [0] * tree_size

            # The number of leaves is always num_nodes + 1
            tree_leaves = [0] * (tree_size + 1)

            for _, node in nodes.iterrows():
                node_idx = node_map[node["ID"]]

                # Feature index (X_test[feature_index])
                feature_index_str = node["Feature"].replace("f", "")
                tree_comp_idxs[node_idx] = int(feature_index_str)

                # Comparison value (rounded to uint8)
                tree_comp_values[node_idx] = int(round(node["Split"]))

                # Child nodes can be leaves or other internal nodes
                left_child_id = node["Yes"]
                right_child_id = node["No"]

                tree_left[node_idx] = node_map.get(
                    left_child_id, leaf_map.get(left_child_id)
                )
                tree_right[node_idx] = node_map.get(
                    right_child_id, leaf_map.get(right_child_id)
                )

            # Scale leaf values (logits) to be uint8_t "votes"
            leaf_gains = leaves["Gain"].to_numpy()
            # Simple scaling: normalize to 0-255 range based on min/max gain in this tree
            min_gain, max_gain = leaf_gains.min(), leaf_gains.max()
            if max_gain - min_gain > 0:
                scaled_leaves = 255 * (leaf_gains - min_gain) / (max_gain - min_gain)
            else:
                scaled_leaves = np.zeros_like(leaf_gains)  # All leaves are the same

            scaled_leaves = np.round(scaled_leaves).astype(int)

            for i in range(len(leaves)):
                tree_leaves[i] = scaled_leaves[i]

            # Add this tree's data to the main lists
            all_comparison_idxs.extend(tree_comp_idxs)
            all_comparison_values.extend(tree_comp_values)
            all_left_children.extend(tree_left)
            all_right_children.extend(tree_right)
            all_leaf_values.extend(tree_leaves)

    # --- Print everything in C format ---
    print(format_c_array("tree_sizes", all_tree_sizes))
    print("\n" + "-" * 40 + "\n")
    print(format_c_array("comparison_idxs", all_comparison_idxs))
    print("\n" + "-" * 40 + "\n")
    print(format_c_array("comparison_values", all_comparison_values))
    print("\n" + "-" * 40 + "\n")
    print(format_c_array("left_children", all_left_children))
    print("\n" + "-" * 40 + "\n")
    print(format_c_array("right_children", all_right_children))
    print("\n" + "-" * 40 + "\n")
    print(format_c_array("leaf_values", all_leaf_values))


# 1. Load the dataset
digits = load_digits()
X, y = digits.data, digits.target

# 2. Define and train the SMALLER XGBoost model
model = xgb.XGBClassifier(
    objective="multi:softmax",
    num_class=10,
    n_estimators=NEW_NUM_TREES,  # Use the smaller number of trees
    max_depth=NEW_MAX_DEPTH,  # Limit the tree depth
    use_label_encoder=False,  # disables label to integer conversion
    eval_metric="mlogloss",  # evaluation function (penetalizes confident wrong answers more)
)

print("Training the model...")
model.fit(X, y)
print("Training complete. Exporting C arrays...\n")

# 3. Export the trained model data to the C format
export_model_to_c_format(model)
