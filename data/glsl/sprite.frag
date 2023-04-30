#version 330

uniform sampler2D sprite_texture;

in vec2 uv;
in vec4 v_color;
in float v_brightness;

out vec4 frag_color;

void main() {
    vec4 tex_color = v_color * texture(sprite_texture, uv);
    frag_color = vec4(tex_color.rgb * v_brightness, tex_color.a);
}