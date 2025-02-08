import os
def validate_audio_file(file_path):
    allowed_formats = [".mp3", ".wav"]
    if not any(file_path.endswitch(fmt) for fmt in allowed_formats):
        raise ValidationError("Invalid audio file format")
    # Check if the file is too large
    if os.path.getsize(file_path) > 10 * 1024 * 1024:
        raise ValidationError("Audio file is too large")
    # check if the file is empty
    if os.path.getsize(file_path) == 0:
        raise ValidationError("Audio file is empty")
    #check if the file is corrupted
    if not is_valid_audio_file(file_path):
        raise ValidationError("Invalid audio file")
    return True

