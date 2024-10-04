#version 150

#pragma include "common.glsl"

uniform sampler2D p3d_Texture0;
uniform sampler2D p3d_Texture1;
uniform sampler2D p3d_Texture2;
uniform sampler2D p3d_Texture3;
uniform int overlay;
uniform vec4 overlayColor;
uniform int destroy;
uniform int highlight;
uniform vec4 p3d_ColorScale;

in vec2 texcoord;

uniform struct {
  vec4 ambient;
} p3d_LightModel;

uniform struct {
  vec4 ambient;
  vec4 diffuse;
  vec3 specular;
  float roughness;
} p3d_Material;

in vec3 vpos;
in vec3 norm;
in vec4 shad[1];

out vec4 p3d_FragColor;

const vec3 SRGB_POWER = vec3(2.2);
const vec3 one3 = vec3(1);

void main() {
  // Sample textures
  vec4 color0 = texture(p3d_Texture0, texcoord);
  vec4 color1 = texture(p3d_Texture1, texcoord);
  vec4 tex = vec4(mix(color0.rgb * p3d_ColorScale.rgb, color1.rgb * overlayColor.rgb, overlay * color1.a), 1);
  if (destroy == 1)
  {
      vec4 overlay_tex = texture(overlay == 0 ? p3d_Texture2 : p3d_Texture3, texcoord);
      tex.rgb *= one3 - overlay_tex.rgb;
  }
  if (highlight == 1)
  {
      vec4 highlight_tex = texture(overlay == 0 ? p3d_Texture1 : p3d_Texture2, texcoord);
      tex = vec4(mix(tex.rgb + highlight_tex.a * highlight_tex.rgb, highlight_tex.rgb, highlight_tex.a), 1);
  }

  p3d_FragColor = p3d_LightModel.ambient * p3d_Material.ambient * tex;

  float alpha = p3d_Material.roughness * p3d_Material.roughness;
  vec3 N = norm;

  for (int i = 0; i < p3d_LightSource.length(); ++i) {
    vec3 diff = p3d_LightSource[i].position.xyz - vpos * p3d_LightSource[i].position.w;
    vec3 L = normalize(diff);
    vec3 V = normalize(-vpos);
    vec3 H = normalize(L + V);

    float NdotL = clamp(dot(N, L), 0.001, 1.0);
    float NdotV = clamp(abs(dot(N, V)), 0.001, 1.0);
    float NdotH = clamp(dot(N, H), 0.0, 1.0);
    float VdotH = clamp(dot(V, H), 0.0, 1.0);

    // Specular term
    float reflectance = max(max(p3d_Material.specular.r, p3d_Material.specular.g), p3d_Material.specular.b);
    float reflectance90 = clamp(reflectance * 25.0, 0.0, 1.0);
    vec3 F = p3d_Material.specular + (vec3(reflectance90) - reflectance) * pow(clamp(1.0 - VdotH, 0.0, 1.0), 5.0);

    // Geometric occlusion term
    float alpha2 = alpha * alpha;
    float attenuationL = 2.0 * NdotL / (NdotL + sqrt(alpha2 + (1.0 - alpha2) * (NdotL * NdotL)));
    float attenuationV = 2.0 * NdotV / (NdotV + sqrt(alpha2 + (1.0 - alpha2) * (NdotV * NdotV)));
    float G = attenuationL * attenuationV;

    // Microfacet distribution term
    float f = (NdotH * alpha2 - NdotH) * NdotH + 1.0;
    float D = alpha2 / (M_PI * f * f);

    // Lambert, energy conserving
    vec3 diffuseContrib = (1.0 - F) * p3d_Material.diffuse.rgb * tex.rgb / M_PI;

    // Cook-Torrance
    vec3 specContrib = F * G * D / (4.0 * NdotL * NdotV);

    // Obtain final intensity as reflectance (BRDF) scaled by the energy of the light (cosine law)
    vec3 color = NdotL * p3d_LightSource[i].color.rgb * (diffuseContrib + specContrib);

    // Shadow
    vec3 shadow = vec3(0.0, 0.0, 0.0);
    float sharpness = 0.01;
    // Quick and dirty gaussian blur
    shadow += textureProj(p3d_LightSource[i].shadowMap, shad[i] + vec4( -0.0326212, -0.0405805, 0, 0) * sharpness);
    shadow += textureProj(p3d_LightSource[i].shadowMap, shad[i] + vec4(-0.0840144, -0.0073580, 0, 0) * sharpness);
    shadow += textureProj(p3d_LightSource[i].shadowMap, shad[i] + vec4(-0.0695914, 0.0457137, 0, 0) * sharpness);
    shadow += textureProj(p3d_LightSource[i].shadowMap, shad[i] + vec4(-0.0203345, 0.0620716, 0, 0) * sharpness);
    shadow += textureProj(p3d_LightSource[i].shadowMap, shad[i] + vec4(0.0962340, -0.0194983, 0, 0) * sharpness);
    shadow += textureProj(p3d_LightSource[i].shadowMap, shad[i] + vec4(0.0473434, -0.0480026, 0, 0) * sharpness);
    shadow += textureProj(p3d_LightSource[i].shadowMap, shad[i] + vec4(0.0519456, 0.0767022, 0, 0) * sharpness);
    shadow += textureProj(p3d_LightSource[i].shadowMap, shad[i] + vec4(0.0185461, -0.0893124, 0, 0) * sharpness);
    shadow += textureProj(p3d_LightSource[i].shadowMap, shad[i] + vec4(0.0507431, 0.0064425, 0, 0) * sharpness);
    shadow += textureProj(p3d_LightSource[i].shadowMap, shad[i] + vec4(0.0896420, 0.0412458, 0, 0) * sharpness);
    shadow += textureProj(p3d_LightSource[i].shadowMap, shad[i] + vec4(-0.0321940, -0.0932615, 0, 0) * sharpness);
    shadow += textureProj(p3d_LightSource[i].shadowMap, shad[i] + vec4(-0.0791559, -0.0597705, 0, 0) * sharpness);
    shadow /= 13.0;
    color *= shadow;

    p3d_FragColor.rgb += color;
  }

  p3d_FragColor.a = 1;

  p3d_FragColor = vec4(pow(p3d_FragColor.rgb, SRGB_POWER), 1.0);
}
