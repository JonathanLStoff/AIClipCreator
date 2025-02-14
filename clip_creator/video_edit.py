from moviepy.editor import VideoFileClip, CompositeVideoClip, ColorClip

def edit_video(input_file, output_file, zoom=1.0, target_size=(720, 1280)):
    """
    Crops a landscape video to a portrait orientation and “zooms in” on the center portion.
    The final video has a black background. Parameters:
      • input_file   : path to the input video file.
      • output_file  : where to write the edited video.
      • zoom         : zoom factor (>1 zooms in more on a smaller crop area).
      • target_size  : tuple (width, height) for the portrait video.
    """
    clip = VideoFileClip(input_file)
    iw, ih = clip.size
    target_w, target_h = target_size
    target_aspect = target_w / target_h

    # Determine the maximum crop that fits the input with the target aspect.
    if ih * target_aspect <= iw:
        # Use full height.
        base_crop_w = ih * target_aspect
        base_crop_h = ih
    else:
        # Use full width.
        base_crop_w = iw
        base_crop_h = iw / target_aspect

    # Apply zoom: a zoom factor > 1 means we crop a smaller region
    crop_w = base_crop_w / zoom
    crop_h = base_crop_h / zoom

    # Center crop coordinates.
    center_x, center_y = iw / 2, ih / 2
    x1 = center_x - crop_w / 2
    y1 = center_y - crop_h / 2
    x2 = center_x + crop_w / 2
    y2 = center_y + crop_h / 2

    # Crop and resize.
    cropped_clip = clip.crop(x1=x1, y1=y1, x2=x2, y2=y2)
    resized_clip = cropped_clip.resize(newsize=target_size)

    # Create a black background and composite the result on it.
    background = ColorClip(size=target_size, color=(0, 0, 0), duration=resized_clip.duration)
    final_clip = CompositeVideoClip([background, resized_clip.set_pos("center")], size=target_size)
    
    final_clip.write_videofile(output_file, codec="libx264")

def get_first_frame_screenshot(input_file, screenshot_path):
    """
    Extracts the first frame from the video and saves it as an image.
    Parameters:
        • input_file     : path to the input video file.
        • screenshot_path: file path for the output image.
    """
    clip = VideoFileClip(input_file)
    # Save the first frame at time t = 0.0 seconds.
    clip.save_frame(screenshot_path, t=0.0)

def crop_video_by_coords(input_file, output_file, x1, y1, x2, y2):
    """
    Crops a video using the provided top-left (x1, y1) and bottom-right (x2, y2) coordinates.
    Parameters:
        • input_file  : path to the input video file.
        • output_file : where to write the cropped video.
        • x1, y1      : coordinates of the top-left corner of the crop box.
        • x2, y2      : coordinates of the bottom-right corner of the crop box.
    """
    clip = VideoFileClip(input_file)
    cropped_clip = clip.crop(x1=x1, y1=y1, x2=x2, y2=y2)
    cropped_clip.write_videofile(output_file, codec="libx264")
    
def crop_video_into_another(background_file, overlay_file, output_file, zoom=1.0, position="center"):
    """
    Crops the overlay video (using the specified zoom factor) and composites it onto the background video.
    Parameters:
        • background_file: path to the background video.
        • overlay_file   : path to the video to be cropped and overlaid.
        • output_file    : where to write the composited video.
        • zoom           : zoom factor (>1 crops a smaller region from the overlay).
        • position       : position for the overlay (any valid moviepy position, e.g., "center", (x, y)).
    """
    bg_clip = VideoFileClip(background_file)
    ov_clip = VideoFileClip(overlay_file)

    # Determine crop dimensions on the overlay clip.
    iw, ih = ov_clip.size
    crop_w = iw / zoom
    crop_h = ih / zoom

    # Calculate center crop coordinates.
    center_x, center_y = iw / 2, ih / 2
    x1 = center_x - crop_w / 2
    y1 = center_y - crop_h / 2
    x2 = center_x + crop_w / 2
    y2 = center_y + crop_h / 2

    # Crop the overlay video.
    cropped_overlay = ov_clip.crop(x1=x1, y1=y1, x2=x2, y2=y2)

    # Ensure the overlay duration matches the background's.
    cropped_overlay = cropped_overlay.set_duration(bg_clip.duration)

    # Composite the cropped overlay over the background at the given position.
    composite_clip = CompositeVideoClip([bg_clip, cropped_overlay.set_position(position)], size=bg_clip.size)
    composite_clip.write_videofile(output_file, codec="libx264")



# Example usage:
if __name__ == "__main__":
    input_video_path = "input_video.mp4"  # Replace with your landscape video file
    output_video_path = "output_portrait.mp4"
    edit_video(input_video_path, output_video_path, zoom=1.2, target_size=(720, 1280))