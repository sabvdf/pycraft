#version 150

#define SAMPLES 16
#define INTENSITY 1.
#define SCALE 2.5
#define BIAS 0.05
#define SAMPLE_RAD 0.02
#define MAX_DISTANCE 0.07

#define MOD3 vec3(.1031,.11369,.13787)

uniform sampler2D rendered;
uniform sampler2D depth;
uniform sampler2D normal;
in vec2 texcoord;

out vec4 p3d_FragColor;


float hash12(vec2 p)
{
	vec3 p3  = fract(vec3(p.xyx) * MOD3);
    p3 += dot(p3, p3.yzx + 19.19);
    return fract((p3.x + p3.y) * p3.z);
}

vec2 hash22(vec2 p)
{
	vec3 p3 = fract(vec3(p.xyx) * MOD3);
    p3 += dot(p3, p3.yzx+19.19);
    return fract(vec2((p3.x + p3.y)*p3.z, (p3.x+p3.z)*p3.y));
}

vec3 getPosition(vec2 uv) {
    float fl = textureLod(depth, vec2(0.), 0.).x;
    float d = textureLod(depth, uv, 0.).w;

    vec2 p = uv*2.-1.;
    mat3 ca = mat3(1.,0.,0.,0.,1.,0.,0.,0.,-1./1.5);
    vec3 rd = normalize( ca * vec3(p,fl) );

	vec3 pos = rd * d;
    return pos;
}

vec3 getNormal(vec2 uv) {
    return textureLod(normal, uv, 0.).xyz;
}

vec2 getRandom(vec2 uv) {
    return normalize(hash22(uv*126.1231) * 2. - 1.);
}

float doAmbientOcclusion(in vec2 tcoord,in vec2 uv, in vec3 p, in vec3 cnorm)
{
    vec3 diff = getPosition(tcoord + uv) - p;
    float l = length(diff);
    vec3 v = diff/l;
    float d = l*SCALE;
    float ao = max(0.0,dot(cnorm,v)-BIAS)*(1.0/(1.0+d));
    ao *= smoothstep(MAX_DISTANCE,MAX_DISTANCE * 0.5, l);
    return ao;

}

float spiralAO(vec2 uv, vec3 p, vec3 n, float rad)
{
    float goldenAngle = 2.4;
    float ao = 0.;
    float inv = 1. / float(SAMPLES);
    float radius = 0.;

    float rotatePhase = hash12( uv*100. ) * 6.28;
    float rStep = inv * rad;
    vec2 spiralUV;

    for (int i = 0; i < SAMPLES; i++) {
        spiralUV.x = sin(rotatePhase);
        spiralUV.y = cos(rotatePhase);
        radius += rStep;
        ao += doAmbientOcclusion(uv, spiralUV * radius, p, n);
        rotatePhase += goldenAngle;
    }
    ao *= inv;
    return ao;
}


void main() {
    vec4 color0 = texture(rendered, texcoord);
    vec4 color1 = texture(normal, texcoord);
    vec4 color2 = texture(depth, texcoord);

    vec3 p = getPosition(texcoord);
    vec3 n = getNormal(texcoord);

    float ao = 0.0;
    float rad = SAMPLE_RAD / p.z;

    ao = spiralAO(texcoord, p, n, rad);

    ao = 1.0 - ao * INTENSITY;

    p3d_FragColor = color0 * ao;
}
