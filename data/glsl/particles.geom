#version 330

layout (points) in;
layout (triangle_strip, max_vertices = 4) out;

in float size[];
in float scale[];
in vec3 color[];

uniform mat4 view;
uniform mat4 projection;
uniform sampler2D sprite_texture;

out float out_scale;
out vec2 uv;
out vec3 v_color;

void main() {
    v_color = color[0];

    vec2 center = gl_in[0].gl_Position.xy;
    float step = size[0] * scale[0] / 2;

    // Upper left
    gl_Position = projection * view * vec4(vec2(-step, step) + center, 0.0, 1.0);
    out_scale = scale[0];
    uv = vec2(0.0, 1.0);
    EmitVertex();

    // lower left
    gl_Position = projection * view * vec4(vec2(-step, -step) + center, 0.0, 1.0);
    out_scale = scale[0];
    uv = vec2(0.0, 0.0);
    EmitVertex();

    // upper right
    gl_Position = projection * view * vec4(vec2(step, step) + center, 0.0, 1.0);
    out_scale = scale[0];
    uv = vec2(1.0, 1.0);
    EmitVertex();

    // lower right
    gl_Position = projection * view * vec4(vec2(step, -step) + center, 0.0, 1.0);
    out_scale = scale[0];
    uv = vec2(1.0, 0.0);
    EmitVertex();

    EndPrimitive();
}