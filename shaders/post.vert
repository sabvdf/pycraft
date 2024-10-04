#version 150

uniform mat4 p3d_ModelViewProjectionMatrix;
in vec2 p3d_MultiTexCoord0;

in vec4 vertex;

out vec2 texcoord;

void main() {
  gl_Position = p3d_ModelViewProjectionMatrix * vertex;
  texcoord = p3d_MultiTexCoord0;
}
