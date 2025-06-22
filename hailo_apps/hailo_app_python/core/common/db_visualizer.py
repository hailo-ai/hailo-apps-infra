# region imports
# Standard library imports
import os

# Third-party imports
import numpy as np
from matplotlib.patches import Ellipse
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
# endregion imports

class DatabaseVisualizer:
    def __init__(self):
        self.db_records = None
        self.global_ax = None
        self.global_pca = None
        self.global_fig = None

    def set_db_records(self, db_records):
        """
        Set the database records to be visualized.

        Args:
            db_records (list): A list of dictionaries containing records.
        """
        self.db_records = db_records

    def create_blank_figure(self):
        # Create a blank figure with a message
        self.global_fig, ax = plt.subplots(figsize=(10, 8))
        ax.set_facecolor("white")  # Set the background color to white
        ax.text(
            0.5, 0.5,  # Position the text in the center
            "No embeddings found.\nRun in 'train' mode first to populate the database with samples.",
            fontsize=12,
            color="black",
            ha="center",  # Horizontal alignment
            va="center",  # Vertical alignment
            wrap=True
        )
        ax.axis("off")  # Turn off the axes
        return self.global_fig  # Return the blank figure

    def add_embeddings_to_existing_plot(self, embeddings, labels=None, cropped_frames=None, mode='cli'):
        """
        Adds multiple embeddings as black points to the existing plot created by visualize.

        Args:
            embeddings (list of numpy.ndarray): The embeddings to add to the plot.
            labels (list of str, optional): The labels corresponding to the embeddings.
            cropped_frames (list of numpy.ndarray, optional): Cropped frames corresponding to the embeddings.
            mode (str): The mode of visualization ('cli' or 'ui').
        """
        if self.global_ax is None or self.global_pca is None:
            print("Error: The plot has not been initialized. Call visualize first.")
            return

        if labels is None:
            labels = [None] * len(embeddings)  # Default to None if no labels are provided

        if cropped_frames is None:
            cropped_frames = [None] * len(embeddings)  # Default to None if no cropped frames are provided

        for embedding, label, cropped_frame in zip(embeddings, labels, cropped_frames):
            # Transform the embedding to 2D using the existing PCA (NumPy-based)
            principal_components, mean = self.global_pca  # Unpack the stored PCA components and mean
            centered_embedding = embedding - mean  # Center the embedding
            reduced_embedding = np.dot(centered_embedding, principal_components)  # Project onto principal components

            # Add the embedding as a black point to the plot
            self.global_ax.scatter(
                reduced_embedding[0],  # X-coordinate
                reduced_embedding[1],  # Y-coordinate
                color='black',         # Black color for the point
                s=100,                 # Size of the point
                label='New Embedding'  # Label for the legend
            )

            # Add a label near the point if provided
            if label is not None and label != 'Unknown':
                self.global_ax.text(
                    reduced_embedding[0] + 0.02,  # X-coordinate offset for better visibility
                    reduced_embedding[1] + 0.02,  # Y-coordinate offset for better visibility
                    label,                        # The label text
                    fontsize=10,                  # Font size
                    color='blue',                 # Label color
                    weight='bold'                 # Font weight
                )

            # If a cropped frame is provided, draw the image near the point
            if cropped_frame is not None:
                img = Image.fromarray(cropped_frame)
                img.thumbnail((30, 30))  # Resize the image to a smaller thumbnail

                # Create a circular mask
                mask = Image.new("L", img.size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, img.size[0], img.size[1]), fill=255)
                img = Image.composite(img, Image.new("RGBA", img.size, (255, 255, 255, 0)), mask)

                # Offset the image to the side of the point
                offset = 0.05  # Adjust this value to control the distance from the point
                image_position = (reduced_embedding[0] + offset, reduced_embedding[1] + offset)

                # Add the circular image to the plot
                imagebox = OffsetImage(img, zoom=0.5)
                ab = AnnotationBbox(imagebox, image_position, frameon=False)
                self.global_ax.add_artist(ab)

        # Update the plot dynamically
        if mode == 'cli':
            self.global_fig.canvas.draw_idle()  # Redraw the canvas
        else:  # UI
            return self.global_fig

    def visualize(self, mode='cli'):
        """
        Creates a 2D visualization of records with their embeddings, confidence circles, and their first sample near the point.
        """
        # Extract all embeddings and perform PCA for dimensionality reduction
        all_embeddings = []
        record_data = {}
        for record in self.db_records:
            samples = record['samples_json']
            embeddings = [np.array(sample['embedding']) for sample in samples]
            images = [sample['sample_path'] for sample in samples]
            all_embeddings.extend(embeddings)
            record_data[record['global_id']] = {
                'name': record['label'],
                'avg_embedding': np.array(record['avg_embedding']),
                'embeddings': embeddings,
                'images': images
            }
        
        if not all_embeddings:
            print("No embeddings found. The plot can't be visualized. Run in 'save' or 'train' mode first to populate the database with samples.")
            if mode == 'ui':  # UI
                return self.create_blank_figure()  # Return the blank figure
            return
        
        # Perform PCA to reduce embeddings to 2D
        reduced_embeddings, principal_components, mean = self.perform_pca(all_embeddings, n_components=2)
        
        # Create a mapping from original embeddings to reduced embeddings
        embedding_map = {tuple(embedding): reduced for embedding, reduced in zip(all_embeddings, reduced_embeddings)}
        
        # Check if global_fig and global_ax are not None
        if self.global_fig is not None and self.global_ax is not None:
            ax = self.global_ax
            ax.clear()  # Clear the existing plot
        else:
            self.global_fig, ax = plt.subplots(figsize=(15, 6))
            self.global_ax = ax
        
        self.global_pca = (principal_components, mean)  # Store principal components and mean for later use
        colors = ['blue', 'green', 'red', 'purple', 'orange', 'brown', 'pink', 'gray', 'cyan', 'magenta']
        
        for idx, (record_id, data) in enumerate(record_data.items()):
            avg_embedding = data['avg_embedding']
            # Transform the average embedding using the principal components
            centered_avg_embedding = avg_embedding - mean
            reduced_avg_embedding = np.dot(centered_avg_embedding, principal_components)
            
            # Calculate the standard deviation for the confidence circle
            reduced_record_embeddings = np.array([embedding_map[tuple(embedding)] for embedding in data['embeddings']])
            std_dev = np.std(reduced_record_embeddings, axis=0)
            
            # Add the confidence circle
            ellipse = Ellipse(
                xy=reduced_avg_embedding,
                width=2 * std_dev[0],  # 2 standard deviations
                height=2 * std_dev[1],
                edgecolor=colors[idx % len(colors)],
                facecolor=colors[idx % len(colors)],
                alpha=0.2
            )
            ax.add_patch(ellipse)

            # Draw all embeddings for the record
            reduced_record_embeddings = np.array([embedding_map[tuple(embedding)] for embedding in data['embeddings']])
            ax.scatter(
                reduced_record_embeddings[:, 0],  # X-coordinates of all embeddings
                reduced_record_embeddings[:, 1],  # Y-coordinates of all embeddings
                color=colors[idx % len(colors)],  # Use the same color for all points of the record
                alpha=0.6,  # Slightly transparent for better visualization
                s=50  # Smaller size for individual points
            )

            # Add the average embedding point with a black outline
            ax.scatter(
                reduced_avg_embedding[0], reduced_avg_embedding[1],
                color=colors[idx % len(colors)], label=data['name'], s=100, edgecolor='black'
            )
            
            # Add the small image near each embedding point
            for embedding, reduced_point, image_path in zip(data['embeddings'], reduced_record_embeddings, data['images']):
                if os.path.exists(image_path):
                    # Open the image
                    img = Image.open(image_path)
                    img.thumbnail((30, 30))  # Resize the image to a smaller thumbnail

                    # Create a circular mask
                    mask = Image.new("L", img.size, 0)
                    draw = ImageDraw.Draw(mask)
                    draw.ellipse((0, 0, img.size[0], img.size[1]), fill=255)
                    img = Image.composite(img, Image.new("RGBA", img.size, (255, 255, 255, 0)), mask)

                    # Offset the image to the side of the point
                    offset = 0.05  # Adjust this value to control the distance from the point
                    image_position = (reduced_point[0] + offset, reduced_point[1] + offset)

                    # Add the circular image to the plot
                    imagebox = OffsetImage(img, zoom=0.5)
                    ab = AnnotationBbox(imagebox, image_position, frameon=False)
                    ax.add_artist(ab)
            
            # Add a label near the average embedding point
            ax.text(
                reduced_avg_embedding[0] + 0.02,  # X-coordinate offset for better visibility
                reduced_avg_embedding[1] + 0.02,  # Y-coordinate offset for better visibility
                data['name'],                    # The label text
                fontsize=10,                      # Font size
                color='black',                    # Label color
                weight='bold'                     # Font weight
            )

        # Add labels and legend
        ax.set_title("2D Visualization of Records with Confidence Circles", fontsize=16)
        # ax.set_xlabel("PCA Component 1", fontsize=12)
        # ax.set_ylabel("PCA Component 2", fontsize=12)

        # Place the legend outside the main plotting area
        ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=10)

        plt.grid(True)
        plt.tight_layout()

        if mode == 'cli':
            plt.ion()
            plt.show(block=False)  # Show the plot
        else:  # UI
            # Ensure grid is always visible (if this is a matplotlib figure)
            if hasattr(self.global_fig, 'gca'):
                ax = self.global_fig.gca()
                ax.grid(True)
            return self.global_fig

    def perform_pca(self, embeddings, n_components=2):
        """
        Perform PCA to reduce the dimensionality of embeddings.

        Args:
            embeddings (np.ndarray): The input data matrix of shape (n_samples, n_features).
            n_components (int): The number of principal components to retain.

        Returns:
            np.ndarray: The reduced embeddings of shape (n_samples, n_components).
            np.ndarray: The principal components (eigenvectors).
            np.ndarray: The mean of the embeddings.
        """
        # Step 1: Center the data (subtract the mean)
        mean = np.mean(embeddings, axis=0)
        centered_embeddings = embeddings - mean

        # Step 2: Compute the covariance matrix
        covariance_matrix = np.cov(centered_embeddings, rowvar=False)

        # Step 3: Compute eigenvalues and eigenvectors
        eigenvalues, eigenvectors = np.linalg.eigh(covariance_matrix)

        # Step 4: Sort eigenvalues and eigenvectors in descending order
        sorted_indices = np.argsort(eigenvalues)[::-1]
        eigenvectors = eigenvectors[:, sorted_indices]

        # Step 5: Select the top n_components eigenvectors
        principal_components = eigenvectors[:, :n_components]

        # Step 6: Project the data onto the principal components
        reduced_embeddings = np.dot(centered_embeddings, principal_components)

        return reduced_embeddings, principal_components, mean