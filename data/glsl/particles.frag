#version 330

in float scale;
in vec2 uv;
in vec4 v_color;

uniform sampler2D sprite_texture;

out vec4 frag_color;

void main() {
    vec4 tex_color = v_color * texture(sprite_texture, uv);
    frag_color = vec4(tex_color.rgb, 1.0 - clamp(scale, 0.0, 1.0));
}