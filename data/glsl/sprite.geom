#version 330

layout (points) in;
layout (triangle_strip, max_vertices = 4) out;

uniform mat4 view;
uniform mat4 projection;

in vec2 size[];
in float rotation[];
in vec4 color[];
in vec2 clip_offset[];
in vec2 clip_size[];
in float brightness[];

out vec2 uv;
out vec4 v_color;
out float v_brightness;

void main() {
    v_color = color[0];
    v_brightness = brightness[0];

    vec2 center = gl_in[0].gl_Position.xy;
    vec2 half_size = size[0] / 2.0;

    // Convert the rotation to radians
    float angle = radians(rotation[0]);

    // Create a 2d rotation matrix
    mat2 rot = mat2(
        cos(angle), sin(angle),
        -sin(angle), cos(angle)
    );

    // Upper left
    gl_Position = projection * view * vec4(rot * vec2(-half_size.x, half_size.y) + center, 0.0, 1.0);
    uv = vec2(clip_offset[0].x, clip_offset[0].y + clip_size[0].y);
    EmitVertex();

    // lower left
    gl_Position = projection * view * vec4(rot * vec2(-half_size.x, -half_size.y) + center, 0.0, 1.0);
    uv = clip_offset[0].xy;
    EmitVertex();

    // upper right
    gl_Position = projection * view * vec4(rot * vec2(half_size.x, half_size.y) + center, 0.0, 1.0);
    uv = vec2(clip_offset[0].x + clip_size[0].x, clip_offset[0].y + clip_size[0].y);
    EmitVertex();

    // lower right
    gl_Position = projection * view * vec4(rot * vec2(half_size.x, -half_size.y) + center, 0.0, 1.0);
    uv = vec2(clip_offset[0].x + clip_size[0].x, clip_offset[0].y);
    EmitVertex();

    EndPrimitive();
}