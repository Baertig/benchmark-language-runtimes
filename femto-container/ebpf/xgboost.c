
/* xgboost benchmark

   Contributor Zachary Susskind <zsusskind@utexas.edu>
   Contributor Konrad Moron <konrad.moron@tum.de>

   This file is part of Embench.

   SPDX-License-Identifier: GPL-3.0-or-later
   */
#include <stdint.h>
#include <stddef.h>
#define SAMPLES_IN_FILE 32
#define SAMPLE_SIZE 64
#define NUM_CLASSES 10
#define NUM_TREES 10

#ifndef SCALE_FACTOR
#define SCALE_FACTOR 1
#endif

typedef struct {
    uint8_t tree_sizes[100];
    uint8_t comparison_idxs[1201];
    uint8_t comparison_values[1201];
    uint8_t left_children[1201];
    uint8_t right_children[1201];
    uint8_t leaf_values[1301];
    uint8_t X_test[SAMPLES_IN_FILE][SAMPLE_SIZE];
    uint8_t Y_test[SAMPLES_IN_FILE];
} context;


// Run inference using XGBoost
static uint8_t __attribute__((always_inline)) predict(const uint8_t *x, context *ctx) {
    uint16_t votes[NUM_CLASSES] = { 0 };
    const uint8_t *tree_sizes = ctx->tree_sizes;
    const uint8_t *comparison_idxs = ctx->comparison_idxs;
    const uint8_t *comparison_values = ctx->comparison_values;
    const uint8_t *left_children = ctx->left_children;
    const uint8_t *right_children = ctx->right_children;
    const uint8_t *leaf_values = ctx->leaf_values;

    size_t tree_idx = 0;
    size_t node_base = 0;
    size_t leaf_base = 0;
    for (size_t i = 0; i < NUM_CLASSES; i++) {
        for (size_t j = 0; j < NUM_TREES; j++) {
            const uint8_t tree_size = tree_sizes[tree_idx];
            const uint8_t *tree_idxs = &comparison_idxs[node_base];
            const uint8_t *tree_values = &comparison_values[node_base];
            const uint8_t *tree_left_children = &left_children[node_base];
            const uint8_t *tree_right_children = &right_children[node_base];
            const uint8_t *tree_leaf_values = &leaf_values[leaf_base];

            // Find leaf node for this tree
            uint8_t node_id = 0;
            while(!(node_id & 0x80)) { // Leaf nodes have ID >= 128
                const uint16_t node_idx = tree_idxs[node_id];
                const uint8_t node_value = tree_values[node_id];
                if (x[node_idx] < node_value) { // Check condition for node
                    node_id = tree_left_children[node_id];
                } else {
                    node_id = tree_right_children[node_id];
                }
            }
            uint8_t leaf_idx = node_id & 0x7F; // Clear MSB to get leaf index
            uint8_t leaf_value = tree_leaf_values[leaf_idx];
            votes[i] += leaf_value;

            tree_idx++;
            node_base += tree_size;
            leaf_base += tree_size+1; // n internal nodes => n+1 leaves
        }
    }

    // return argmax of votes
    uint8_t class_idx = 0;
    uint16_t max_votes = votes[0];
    for (uint8_t i = 1; i < 10; i++) {
        if (votes[i] > max_votes) {
            class_idx = i;
            max_votes = votes[i];
        }
    }

    return class_idx;
}

int benchmark(context *ctx) {
    unsigned int sf = SCALE_FACTOR;
    size_t correct = 0;
	for (unsigned int sf_cnt = 0; sf_cnt < sf; sf_cnt++) {
        for (volatile size_t i = 0; i < SAMPLES_IN_FILE; i++) {
		  uint8_t predicted = predict(ctx->X_test[i], ctx);
		  uint8_t label = ctx->Y_test[i];
		  if (predicted == label)
                correct++;
		}
	}

    return correct == 2 * SCALE_FACTOR;
}