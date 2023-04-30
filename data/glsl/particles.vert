#version 330

in vec2 in_position;
in vec2 in_direction;
in float in_size;
in float in_scale;
in vec4 in_color;

uniform mat4 view;
uniform mat4 projection;

uniform sampler2D sprite_texture;

out float size;
out float scale;
out vec4 color;

void main() {
    gl_Position = vec4(in_position, 0.0, 1.0);

    size = in_size;
    scale = in_scale;
    color = in_color;
}