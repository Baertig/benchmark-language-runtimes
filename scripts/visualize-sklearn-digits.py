import matplotlib.pyplot as plt
from sklearn.datasets import load_digits


def visualize_training_samples(dataset, num_samples=20):
    """
    Displays a sample of images and labels from the scikit-learn digits dataset.
    """
    # Create a grid to display the images. Let's do 4 rows and 5 columns.
    fig, axes = plt.subplots(4, 5, figsize=(8, 7))

    # Flatten the axes array for easy iteration
    axes = axes.flatten()

    # The dataset.images attribute contains the 8x8 images directly
    images_and_labels = list(zip(dataset.images, dataset.target))

    print(f"Displaying the first {num_samples} samples from the training dataset...")

    for i, (image, label) in enumerate(images_and_labels[:num_samples]):
        ax = axes[i]

        # Display the image. 'gray_r' (reversed gray) shows 0 as white.
        ax.imshow(image, cmap=plt.cm.gray_r, interpolation="nearest")

        # Remove axis ticks for a cleaner look
        ax.set_xticks([])
        ax.set_yticks([])

        # Set the title of each subplot to its correct label
        ax.set_title(f"Label: {label}")

    # Adjust layout and show the plot
    plt.tight_layout()
    plt.show()


# --- Main execution ---
if __name__ == "__main__":
    # Load the digits dataset from scikit-learn
    digits_dataset = load_digits()

    # Visualize the first 20 samples
    visualize_training_samples(digits_dataset, num_samples=20)
    print("Done.")
