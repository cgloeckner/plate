#version 330

in vec2 in_position;
in vec2 in_origin;
in vec2 in_size;
in float in_scale;
in float in_rotation;
in vec4 in_color;
in vec2 in_clip_offset;
in vec2 in_clip_size;
in float in_brightness;

out vec2 origin;
out vec2 size;
out float rotation;
out vec4 color;
out vec2 clip_offset;
out vec2 clip_size;
out float brightness;

void main() {
    gl_Position = vec4(in_position, 0, 1);
    origin = in_origin;
    size = in_size;
    rotation = in_rotation;
    color = in_color;
    clip_offset = in_clip_offset;
    clip_size = in_clip_size;
    brightness = in_brightness;
}