from PIL import Image
import os

def combine_images_two_columns(folder_path, output_path):
    # Load all the images in the folder that end with .jpg
    images = [Image.open(os.path.join(folder_path, f)) for f in os.listdir(folder_path) if f.endswith('.jpg')]
    
    # Split the images into two columns
    left_column_images = images[::2]  # Images at even indices
    right_column_images = images[1::2]  # Images at odd indices

    # Calculate total height for each column
    left_column_height = sum(image.height for image in left_column_images)
    right_column_height = sum(image.height for image in right_column_images)

    # Calculate the maximum width for both columns to align them properly
    max_width_left = max(image.width for image in left_column_images)
    max_width_right = max(image.width for image in right_column_images)

    # Create a new image with the appropriate size
    total_height = max(left_column_height, right_column_height)
    combined_image = Image.new('RGB', (max_width_left + max_width_right, total_height))

    # Paste the images in the left column
    y_offset_left = 0
    for image in left_column_images:
        combined_image.paste(image, (0, y_offset_left))
        y_offset_left += image.height

    # Paste the images in the right column
    y_offset_right = 0
    for image in right_column_images:
        combined_image.paste(image, (max_width_left, y_offset_right))
        y_offset_right += image.height

    # Save the combined image
    combined_image.save(output_path)

# Example usage
folder_path = './output'  # Change to your folder path
output_path = 'combined_result.jpg'  # Output image path
combine_images_two_columns(folder_path, output_path)
