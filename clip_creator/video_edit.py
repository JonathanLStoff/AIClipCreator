from moviepy import VideoFileClip, CompositeVideoClip, ColorClip, TextClip
from moviepy.video.fx import Crop, Resize
from random import randint
from clip_creator.conf import LOGGER

def edit_video(input_file, output_file, zoom=1.0, target_size=(720, 1280), start_time=0, end_time=60, text:str=""):
    """
    Crops a landscape video to a portrait orientation and “zooms in” on the center portion.
    The final video has a black background. Parameters:
      • input_file   : path to the input video file.
      • output_file  : where to write the edited video.
      • zoom         : zoom factor (>1 zooms in more on a smaller crop area).
      • target_size  : tuple (width, height) for the portrait video.
    """
    clip = VideoFileClip(input_file).subclipped(start_time, end_time)
    LOGGER.info(f"Video duration: {end_time-start_time} seconds")
    iw, ih = clip.size
    target_h, target_w = target_size
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
    
    
    cropped = Crop(x1=x1, y1=y1, x2=x2, y2=y2)
    cropped_clip = cropped.apply(clip)
    cropped_clip.with_effects([Resize(0.3)])
    
    # Create a black background and composite the result on it.
    #background = ColorClip(size=target_size, color=(0, 0, 0), duration=cropped_clip.duration).with_fps(cropped_clip.fps)
    #final_clip = background.overlay(cropped_clip, position=("center", "center"))
    text_commm = TextClip(text, font_size=70, color='white', duration=cropped_clip.duration, stroke_color='black', stroke_width=5).with_position("top").rotate(randint(-10, 10))
    final_clip = CompositeVideoClip([cropped_clip.with_position("center"), text_commm], size=target_size, bg_color=(0, 0, 0))
    
    final_clip.write_videofile(output_file.replace(".mp4", "_final.mp4"), codec="libx264")

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

    cropped_overlay = ov_clip.fx(vfx.crop, x1=x1, y1=y1, x2=x2, y2=y2)
    #cropped_overlay = ov_clip.crop(x1=x1, y1=y1, x2=x2, y2=y2)

    # Ensure the overlay duration matches the background's.
    cropped_overlay = cropped_overlay.set_duration(bg_clip.duration)

    # Composite the cropped overlay over the background at the given position.
    composite_clip = CompositeVideoClip([bg_clip, cropped_overlay.set_position(position)], size=bg_clip.size)
    composite_clip.write_videofile(output_file, codec="libx264")

def add_text_to_video(video_path, text, font, fontsize, color, outline_color, outline_width, position, rotation):
    """
    Adds text to a video with customizable rotation, position, outline, and font.

    Args:
        video_path: Path to the video file.
        text: The text to be added.
        font: The font to use (e.g., "Arial", "Impact", path to a .ttf file).
        fontsize: The font size.
        color: The text color (e.g., "white", "red", "#00FF00").
        outline_color: The color of the text outline.
        outline_width: The width of the text outline.
        position: The position of the text (e.g., "center", ("left", "top"), (x,y) coordinates).
        rotation: The rotation angle in degrees (e.g., 0, 90, 180).
    """

    try:
        clip = VideoFileClip(video_path)
    except Exception as e:
        print(f"Error opening video: {e}")
        return

    txt_clip = TextClip(text,
                        font=font,
                        fontsize=fontsize,
                        color=color,
                        stroke_color=outline_color,  # Outline color
                        stroke_width=outline_width)   # Outline width

    txt_clip = txt_clip.set_pos(position).set_duration(clip.duration).rotate(rotation)

    final_clip = CompositeVideoClip([clip, txt_clip])

    # You can choose the output video codec and quality
    output_path = "output_video.mp4" # or any other name/path
    final_clip.write_videofile(output_path, codec="libx264", fps=clip.fps, audio_codec="aac") # Adjust codec if needed

    clip.close()  # Close the video clip to release resources
    final_clip.close() # Close the final clip
    print(f"Video with text saved to {output_path}")

# Example usage:
if __name__ == "__main__":
    input_video_path = "input_video.mp4"  # Replace with your landscape video file
    output_video_path = "output_portrait.mp4"
    edit_video(input_video_path, output_video_path, zoom=1.2, target_size=(720, 1280))