// Fractal surface projection for TouchDesigner GLSL POP.
// INPUT: box-distributed P. OUTPUT: P, N, Color, PointScale.

uniform vec4 uFractalParams; // x type 0..3, y power 2..16, z iterations 1..16, w scale -5..5
uniform vec4 uFoldParams;    // x fold limit, y min radius, z bailout, w Mandelbox iso level
uniform vec4 uProjectParams; // x steps 1..16, y epsilon .001..1, z seed extent 0.5..8, w max travel 0.1..8
uniform vec4 uColorA;        // rgb palette base, w phase
uniform vec4 uColorB;        // rgb palette amplitude, w saturation
uniform vec4 uColorC;        // rgb palette frequency, w surface dither 0..2

const float TAU = 6.28318530718;

float mandelbulb(vec3 p, out float orbit)
{
    vec3 z = p;
    float dr = 1.0;
    float r = 0.0;
    orbit = 1e9;
    int count = clamp(int(round(uFractalParams.z)), 1, 32);
    for (int i = 0; i < 32; ++i) {
        if (i >= count) break;
        r = length(z);
        orbit = min(orbit, r);
        if (r > uFoldParams.z) break;
        float theta = acos(clamp(z.z / max(r, 1e-6), -1.0, 1.0));
        float phi = atan(z.y, z.x);
        float power = uFractalParams.y;
        dr = pow(r, power - 1.0) * power * dr + 1.0;
        float zr = pow(r, power);
        theta *= power;
        phi *= power;
        z = zr * vec3(sin(theta) * cos(phi), sin(theta) * sin(phi), cos(theta)) + p;
    }
    return 0.5 * log(max(r, 1e-6)) * r / max(dr, 1e-6);
}

float mandelbox(vec3 p, out float orbit)
{
    vec3 z = p;
    float dr = 1.0;
    float minRadius2 = max(uFoldParams.y * uFoldParams.y, 1e-4);
    orbit = 1e9;
    int count = clamp(int(round(uFractalParams.z)), 1, 32);
    for (int i = 0; i < 32; ++i) {
        if (i >= count) break;
        z = clamp(z, -uFoldParams.x, uFoldParams.x) * 2.0 - z;
        float radius2 = dot(z, z);
        orbit = min(orbit, radius2);
        if (radius2 < minRadius2) {
            float factor = 1.0 / minRadius2;
            z *= factor; dr *= factor;
        } else if (radius2 < 1.0) {
            float factor = 1.0 / radius2;
            z *= factor; dr *= factor;
        }
        z = z * uFractalParams.w + p;
        dr = dr * abs(uFractalParams.w) + 1.0;
        if (dot(z, z) > uFoldParams.z * uFoldParams.z) break;
    }
    return length(z) / max(abs(dr), 1e-6);
}

float sierpinski(vec3 p, out float orbit)
{
    vec3 z = p;
    float radius = 0.0;
    float scale = max(abs(uFractalParams.w), 1.01);
    orbit = 1e9;
    int count = clamp(int(round(uFractalParams.z)), 1, 16);
    for (int i = 0; i < 16; ++i) {
        if (i >= count) break;
        if (z.x + z.y < 0.0) z.xy = -z.yx;
        if (z.x + z.z < 0.0) z.xz = -z.zx;
        if (z.y + z.z < 0.0) z.yz = -z.zy;
        z = z * scale - vec3(scale - 1.0);
        radius = length(z);
        orbit = min(orbit, radius);
    }
    return radius * pow(scale, -float(count));
}

float sdBox(vec3 p, vec3 b)
{
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0);
}

float menger(vec3 p, out float orbit)
{
    float d = sdBox(p, vec3(1.0));
    float scale = 1.0;
    orbit = 1e9;
    int count = clamp(int(round(uFractalParams.z)), 1, 10);
    for (int i = 0; i < 10; ++i) {
        if (i >= count) break;
        vec3 cell = mod(p * scale, 2.0) - 1.0;
        scale *= 3.0;
        vec3 c = abs(1.0 - 3.0 * abs(cell));
        float cut = (min(max(c.x, c.y), min(max(c.y, c.z), max(c.z, c.x))) - 1.0) / scale;
        d = max(d, cut);
        orbit = min(orbit, length(cell));
    }
    return d;
}

float distanceEstimator(vec3 p, out float orbit)
{
    int kind = clamp(int(round(uFractalParams.x)), 0, 3);
    if (kind == 0) return mandelbulb(p, orbit);
    if (kind == 1) return mandelbox(p, orbit) - uFoldParams.w;
    if (kind == 2) return sierpinski(p, orbit);
    return menger(p, orbit);
}

vec3 estimateNormal(vec3 p, float e)
{
    vec2 h = vec2(e, -e);
    float unused;
    return normalize(h.xyy * distanceEstimator(p + h.xyy, unused)
        + h.yyx * distanceEstimator(p + h.yyx, unused)
        + h.yxy * distanceEstimator(p + h.yxy, unused)
        + h.xxx * distanceEstimator(p + h.xxx, unused));
}

vec3 palette(float t)
{
    vec3 colorValue = uColorA.rgb + uColorB.rgb * cos(TAU * (uColorC.rgb * t + uColorA.w));
    float luma = dot(colorValue, vec3(0.299, 0.587, 0.114));
    return mix(vec3(luma), colorValue, uColorB.w);
}

vec2 hashPoint(uint id)
{
    vec2 value = sin(vec2(float(id) + 17.0, float(id) + 71.0) * vec2(12.9898, 78.233));
    return fract(value * 43758.5453) * 2.0 - 1.0;
}

vec3 sphereDirection(uint id)
{
    float count = max(float(TDNumElements()), 1.0);
    float indexValue = float(id) + 0.5;
    float z = 1.0 - 2.0 * indexValue / count;
    float angle = indexValue * 2.39996322973;
    float radius = sqrt(max(1.0 - z * z, 0.0));
    return vec3(radius * cos(angle), radius * sin(angle), z);
}

uint hashUint(uint value)
{
    value ^= value >> 16;
    value *= 0x7feb352du;
    value ^= value >> 15;
    value *= 0x846ca68bu;
    value ^= value >> 16;
    return value;
}

vec3 sierpinskiPoint(uint id, int iterations)
{
    const vec3 vertices[4] = vec3[4](
        vec3(0.0, 1.0, 0.0),
        vec3(0.942809, -0.333333, 0.0),
        vec3(-0.471405, -0.333333, 0.816497),
        vec3(-0.471405, -0.333333, -0.816497)
    );
    uint state = hashUint(id + 1u);
    vec3 pointValue = vec3(0.0);
    int count = clamp(iterations * 2, 8, 32);
    for (int i = 0; i < 32; ++i)
    {
        if (i >= count) break;
        state = hashUint(state + uint(i) + 1u);
        pointValue = 0.5 * (pointValue + vertices[int(state & 3u)]);
    }
    return pointValue * (uProjectParams.z * 0.35);
}

void main()
{
    uint id = TDIndex();
    if (id >= TDNumElements()) return;
    int kind = clamp(int(round(uFractalParams.x)), 0, 3);
    vec3 seed = TDIn_P();
    vec3 p = seed;
    float epsilonValue = max(uProjectParams.y, uProjectParams.z / 8192.0);
    // Keep the accepted shell thin when projection epsilon is raised. A wide
    // final band admits nearby DE lobes as a smaller internal fractal.
    float acceptanceEpsilon = min(epsilonValue, max(uProjectParams.z / 512.0, 0.001));
    float previousDistance = 1e9;
    float orbit = 0.0;
    int steps = clamp(int(round(uProjectParams.x)), 1, 16);

    // A tetrahedral IFS produces the Sierpinski point set directly. Treating
    // its unsigned fold estimate as a signed surface caused box-plane collapse.
    if (kind == 2)
    {
        p = sierpinskiPoint(id, int(round(uFractalParams.z)));
        vec3 normalValue = normalize(p + vec3(1e-6));
        float structure = length(p) / max(uProjectParams.z, 1e-6);
        vec3 colorValue = max(palette(structure), vec3(0.0));
        float diffuse = 0.3 + 0.7 * abs(dot(normalValue, normalize(vec3(0.45, 0.72, 0.53))));
        P[id] = p;
        N[id] = normalValue;
        Color[id] = vec4(colorValue * diffuse, 1.0);
        PointScale[id] = 0.72;
        return;
    }

    bool raySample = kind == 3;
    if (raySample) {
        vec3 inward = -sphereDirection(id);
        p = -inward * uProjectParams.z;
        for (int i = 0; i < 64; ++i) {
            float d = distanceEstimator(p, orbit);
            previousDistance = d;
            if (abs(d) <= epsilonValue) break;
            p += inward * clamp(abs(d), epsilonValue * 0.25, 0.25);
        }
    } else {
        for (int i = 0; i < 16; ++i) {
            if (i >= steps) break;
            float d = distanceEstimator(p, orbit);
            vec3 normalValue = estimateNormal(p, epsilonValue * 0.5);
            p -= normalValue * clamp(d, -0.25, 0.25);
            previousDistance = d;
        }
    }
    // Break projection bands in surface space, then pull the point back to the
    // zero-set. The offset is deterministic, so a static fractal does not buzz.
    float preliminaryDistance = distanceEstimator(p, orbit);
    if (abs(preliminaryDistance) <= acceptanceEpsilon * 4.0 && uColorC.w > 0.0)
    {
        vec3 preliminaryNormal = estimateNormal(p, epsilonValue * 0.5);
        vec3 axis = abs(preliminaryNormal.y) < 0.9 ? vec3(0.0, 1.0, 0.0) : vec3(1.0, 0.0, 0.0);
        vec3 tangentA = normalize(cross(axis, preliminaryNormal));
        vec3 tangentB = cross(preliminaryNormal, tangentA);
        vec2 offsetValue = hashPoint(id);
        p += (tangentA * offsetValue.x + tangentB * offsetValue.y) * epsilonValue * uColorC.w;
        for (int correction = 0; correction < 2; ++correction)
        {
            float correctionDistance = distanceEstimator(p, orbit);
            vec3 correctionNormal = estimateNormal(p, epsilonValue * 0.5);
            p -= correctionNormal * clamp(correctionDistance, -epsilonValue * 4.0, epsilonValue * 4.0);
        }
    }

    float finalDistance = distanceEstimator(p, orbit);
    float travel = length(p - seed);
    bool converged = abs(finalDistance) <= acceptanceEpsilon * (raySample ? 4.0 : 2.0);
    converged = converged && abs(finalDistance) <= abs(previousDistance) + acceptanceEpsilon;
    converged = converged && (raySample || travel <= uProjectParams.w);
    converged = converged && all(lessThan(abs(p), vec3(uProjectParams.z * 1.25)));
    if (!converged) {
        P[id] = p; N[id] = vec3(0.0, 1.0, 0.0);
        Color[id] = vec4(0.0); PointScale[id] = 0.0; return;
    }
    vec3 normalValue = estimateNormal(p, epsilonValue * 0.5);
    vec3 lightDir = normalize(vec3(0.45, 0.72, 0.53));
    float diffuse = 0.25 + 0.75 * abs(dot(normalValue, lightDir));
    float confidence = 1.0 - clamp(abs(finalDistance) / max(acceptanceEpsilon * 2.0, 1e-6), 0.0, 1.0);
    float modeGain = kind == 1 ? 2.2 : 1.0;
    vec3 colorValue = max(palette(orbit * 0.35), vec3(0.0)) * diffuse * modeGain;
    vec3 outputPosition = kind == 1 ? p * 0.55 : p;
    P[id] = outputPosition;
    N[id] = normalValue;
    Color[id] = vec4(colorValue, confidence);
    PointScale[id] = mix(0.25, 1.0, confidence);
}
