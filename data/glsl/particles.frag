#version 330

uniform sampler2D sprite_texture;

in float scale;
in vec2 uv;
in vec3 v_color;

out vec4 frag_color;

void main() {
    vec4 tex_color = texture(sprite_texture, uv);
    frag_color = vec4(tex_color.rgb * v_color * (1 - scale), tex_color.a);
}
