using UnityEngine;
using UnityEditor;
using System.Collections.Generic;
using System.Text;
using System.IO;
using System.Linq;

using System.Globalization;

#if UNITY_EDITOR
public class UnityMotionStateExporter : EditorWindow
{
    [MenuItem("Tools/Motion State Inspector/Export Current Frame")]
    public static void ExportCurrentFrame()
    {
        string path = EditorUtility.SaveFilePanel("Export Motion State", "", "raw_state.json", "json");
        if (string.IsNullOrEmpty(path)) return;

        string json = GenerateSceneStateJson();
        File.WriteAllText(path, json);
        Debug.Log("Exported Motion State to " + path);
    }

    static string GenerateSceneStateJson()
    {
        StringBuilder sb = new StringBuilder();
        sb.Append("{\n");
        
        // Meta
        sb.Append("  \"meta\": {\n");
        sb.Append($"    \"blender_version\": \"unity-{Application.unityVersion}\",\n");
        sb.Append($"    \"scene_name\": \"{UnityEngine.SceneManagement.SceneManager.GetActiveScene().name}\",\n");
        sb.Append("    \"current_frame\": 1,\n");
        sb.Append("    \"fps\": 60,\n");
        sb.Append("    \"frame_start\": 1,\n");
        sb.Append("    \"frame_end\": 1,\n");
        sb.Append("    \"render_engine\": \"unity\"\n");
        sb.Append("  },\n");

        // Actors
        sb.Append("  \"actors\": [\n");
        
        HashSet<GameObject> processedRoots = new HashSet<GameObject>();
        List<GameObject> actorRoots = new List<GameObject>();
        
        // Find Animators
        foreach (var anim in Object.FindObjectsOfType<Animator>())
        {
            actorRoots.Add(anim.gameObject);
            processedRoots.Add(anim.gameObject);
        }
        
        // Find standalone Renderers
        foreach (var r in Object.FindObjectsOfType<Renderer>())
        {
            if (r is MeshRenderer || r is SkinnedMeshRenderer)
            {
                var root = r.transform.root.gameObject;
                if (!processedRoots.Contains(root))
                {
                    actorRoots.Add(root);
                    processedRoots.Add(root);
                }
            }
        }

        List<string> actorJsons = new List<string>();
        foreach (var root in actorRoots)
        {
            actorJsons.Add(ExportActor(root));
        }

        sb.Append(string.Join(",\n", actorJsons));
        sb.Append("\n  ],\n");

        // Spatial
        sb.Append("  \"spatial\": {\n");
        sb.Append("    \"camera\": {\n");
        Camera cam = Camera.main;
        if (cam != null)
        {
            Vector3 camLoc = ToBlender(cam.transform.position);
            Vector3 camRot = cam.transform.eulerAngles;
            sb.Append($"      \"name\": \"{cam.name}\",\n");
            sb.Append($"      \"location\": [{FormatFloat(camLoc.x)}, {FormatFloat(camLoc.y)}, {FormatFloat(camLoc.z)}],\n");
            sb.Append($"      \"rotation_euler\": [{FormatFloat(camRot.x)}, {FormatFloat(camRot.y)}, {FormatFloat(camRot.z)}],\n");
            sb.Append($"      \"focal_length\": {FormatFloat(cam.fieldOfView)}\n");
        }
        else
        {
            sb.Append("      \"name\": \"\",\n      \"location\": [0,0,0],\n      \"rotation_euler\": [0,0,0],\n      \"focal_length\": 50\n");
        }
        sb.Append("    },\n");
        
        // Actor distances
        sb.Append("    \"actor_distances\": [\n");
        List<string> distances = new List<string>();
        for (int i = 0; i < actorRoots.Count; i++)
        {
            for (int j = i + 1; j < actorRoots.Count; j++)
            {
                float d = Vector3.Distance(actorRoots[i].transform.position, actorRoots[j].transform.position);
                distances.Add($"      {{\"from_actor\": \"{actorRoots[i].name}\", \"to_actor\": \"{actorRoots[j].name}\", \"distance\": {FormatFloat(d)}}}");
            }
        }
        sb.Append(string.Join(",\n", distances));
        sb.Append("\n    ]\n");
        
        sb.Append("  }\n");
        sb.Append("}\n");
        return sb.ToString();
    }

    static string ExportActor(GameObject go)
    {
        StringBuilder sb = new StringBuilder();
        sb.Append("    {\n");
        sb.Append($"      \"name\": \"{go.name}\",\n");
        sb.Append($"      \"type\": \"{(go.GetComponent<Animator>() != null ? "ARMATURE" : "MESH")}\",\n");
        sb.Append($"      \"visible\": {go.activeInHierarchy.ToString().ToLower()},\n");
        sb.Append("      \"world_matrix\": [\n        [1,0,0,0],\n        [0,1,0,0],\n        [0,0,1,0],\n        [0,0,0,1]\n      ],\n");

        // Mesh
        Renderer[] renderers = go.GetComponentsInChildren<Renderer>();
        Bounds bounds = new Bounds(go.transform.position, Vector3.zero);
        bool first = true;
        int vertexCount = 0;
        List<string> materials = new List<string>();
        bool hasArmatureMod = go.GetComponentInChildren<SkinnedMeshRenderer>() != null;

        foreach (var r in renderers)
        {
            if (r is MeshRenderer || r is SkinnedMeshRenderer)
            {
                if (first) { bounds = r.bounds; first = false; }
                else { bounds.Encapsulate(r.bounds); }

                foreach (var mat in r.sharedMaterials)
                {
                    if (mat != null) materials.Add($"\"{mat.name}\"");
                }

                if (r is MeshRenderer mr && mr.GetComponent<MeshFilter>() != null && mr.GetComponent<MeshFilter>().sharedMesh != null)
                {
                    vertexCount += mr.GetComponent<MeshFilter>().sharedMesh.vertexCount;
                }
                else if (r is SkinnedMeshRenderer smr && smr.sharedMesh != null)
                {
                    vertexCount += smr.sharedMesh.vertexCount;
                }
            }
        }
        
        Vector3 wMin = ToBlender(bounds.min);
        Vector3 wMax = ToBlender(bounds.max);
        
        // Correct min/max after coordinate flip (Y and Z swapped, Z negated)
        float wxMin = Mathf.Min(wMin.x, wMax.x);
        float wxMax = Mathf.Max(wMin.x, wMax.x);
        float wyMin = Mathf.Min(wMin.y, wMax.y);
        float wyMax = Mathf.Max(wMin.y, wMax.y);
        float wzMin = Mathf.Min(wMin.z, wMax.z);
        float wzMax = Mathf.Max(wMin.z, wMax.z);
        
        Vector3 dims = new Vector3(wxMax - wxMin, wyMax - wyMin, wzMax - wzMin);

        sb.Append("      \"mesh\": {\n");
        sb.Append($"        \"vertex_count\": {vertexCount},\n");
        sb.Append("        \"face_count\": 0,\n");
        sb.Append("        \"edge_count\": 0,\n");
        sb.Append("        \"bbox_min\": [0,0,0],\n");
        sb.Append("        \"bbox_max\": [0,0,0],\n");
        sb.Append($"        \"bbox_world_min\": [{FormatFloat(wxMin)}, {FormatFloat(wyMin)}, {FormatFloat(wzMin)}],\n");
        sb.Append($"        \"bbox_world_max\": [{FormatFloat(wxMax)}, {FormatFloat(wyMax)}, {FormatFloat(wzMax)}],\n");
        sb.Append($"        \"dimensions\": [{FormatFloat(dims.x)}, {FormatFloat(dims.y)}, {FormatFloat(dims.z)}],\n");
        sb.Append($"        \"materials\": [{string.Join(", ", materials.Distinct())}],\n");
        sb.Append($"        \"has_armature_modifier\": {hasArmatureMod.ToString().ToLower()},\n");
        sb.Append($"        \"armature_name\": \"{(hasArmatureMod ? go.name : "")}\",\n");
        sb.Append("        \"vertex_groups_count\": 0\n");
        sb.Append("      },\n");

        // Armature
        Animator anim = go.GetComponent<Animator>();
        if (anim != null)
        {
            Transform[] bones = go.GetComponentsInChildren<Transform>();
            sb.Append("      \"armature\": {\n");
            sb.Append($"        \"bone_count\": {bones.Length},\n");
            sb.Append("        \"bones\": [\n");
            List<string> boneJsons = new List<string>();
            foreach (Transform b in bones)
            {
                boneJsons.Add(ExportBone(b, go.transform));
            }
            sb.Append(string.Join(",\n", boneJsons));
            sb.Append("\n        ]\n      },\n");
            
            // Pose (same as armature for simplicity in this format)
            sb.Append("      \"pose\": {\n");
            sb.Append("        \"pose_bones\": [\n");
            List<string> poseJsons = new List<string>();
            foreach (Transform b in bones)
            {
                poseJsons.Add(ExportPoseBone(b));
            }
            sb.Append(string.Join(",\n", poseJsons));
            sb.Append("\n        ]\n      }\n");
        }
        else
        {
            sb.Append("      \"armature\": { \"bone_count\": 0, \"bones\": [] },\n");
            sb.Append("      \"pose\": { \"pose_bones\": [] }\n");
        }

        sb.Append("    }");
        return sb.ToString();
    }

    static string ExportBone(Transform bone, Transform root)
    {
        Vector3 head = ToBlender(bone.localPosition);
        Vector3 worldHead = ToBlender(bone.position);
        
        Vector3 worldTail;
        if (bone.childCount > 0)
        {
            worldTail = ToBlender(bone.GetChild(0).position);
        }
        else
        {
            worldTail = ToBlender(bone.position + bone.forward * 0.1f);
        }
        Vector3 tail = worldTail - worldHead; // approx local

        float length = Vector3.Distance(worldHead, worldTail);
        string parentName = bone.parent != null && bone != root ? $"\"{bone.parent.name}\"" : "null";

        StringBuilder sb = new StringBuilder();
        sb.Append("          {\n");
        sb.Append($"            \"name\": \"{bone.name}\",\n");
        sb.Append($"            \"parent\": {parentName},\n");
        sb.Append($"            \"head\": [{FormatFloat(head.x)}, {FormatFloat(head.y)}, {FormatFloat(head.z)}],\n");
        sb.Append($"            \"tail\": [{FormatFloat(tail.x)}, {FormatFloat(tail.y)}, {FormatFloat(tail.z)}],\n");
        sb.Append($"            \"world_head\": [{FormatFloat(worldHead.x)}, {FormatFloat(worldHead.y)}, {FormatFloat(worldHead.z)}],\n");
        sb.Append($"            \"world_tail\": [{FormatFloat(worldTail.x)}, {FormatFloat(worldTail.y)}, {FormatFloat(worldTail.z)}],\n");
        sb.Append("            \"local_rotation_euler\": [0,0,0],\n");
        sb.Append("            \"world_rotation_quaternion\": [1,0,0,0],\n");
        sb.Append($"            \"length\": {FormatFloat(length)},\n");
        sb.Append("            \"is_deform\": true,\n");
        sb.Append("            \"constraints\": []\n");
        sb.Append("          }");
        return sb.ToString();
    }

    static string ExportPoseBone(Transform bone)
    {
        Vector3 loc = ToBlender(bone.position);
        // Note: For advanced joint angles we might want to export quaternions,
        // but for facing and morphology, positions are sufficient.
        StringBuilder sb = new StringBuilder();
        sb.Append("          {\n");
        sb.Append($"            \"name\": \"{bone.name}\",\n");
        sb.Append($"            \"location\": [{FormatFloat(loc.x)}, {FormatFloat(loc.y)}, {FormatFloat(loc.z)}],\n");
        sb.Append("            \"rotation_quaternion\": [1,0,0,0],\n");
        sb.Append($"            \"scale\": [{FormatFloat(bone.localScale.x)}, {FormatFloat(bone.localScale.y)}, {FormatFloat(bone.localScale.z)}],\n");
        sb.Append("            \"world_matrix\": [\n              [1,0,0,0],\n              [0,1,0,0],\n              [0,0,1,0],\n              [0,0,0,1]\n            ]\n");
        sb.Append("          }");
        return sb.ToString();
    }

    static string FormatFloat(float f)
    {
        return f.ToString("F4", CultureInfo.InvariantCulture);
    }

    static Vector3 ToBlender(Vector3 unityVec)
    {
        // Unity is X-Right, Y-Up, Z-Forward (Left Handed)
        // Blender is X-Right, Y-Forward, Z-Up (Right Handed)
        // Mapping: X_b = X_u, Y_b = -Z_u, Z_b = Y_u
        return new Vector3(unityVec.x, -unityVec.z, unityVec.y);
    }
}
#endif
