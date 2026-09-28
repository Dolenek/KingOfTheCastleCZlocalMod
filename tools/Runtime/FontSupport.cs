using System;
using System.Collections.Generic;
using System.IO;
using TMPro;
using UnityEngine;
using UnityEngine.TextCore.LowLevel;

namespace Kotc.Czech
{
    public static class FontLoader
    {
        private static readonly Dictionary<int, string> Paths = new Dictionary<int, string>();

        internal static void Register(Font carrier, string path)
        {
            Paths.Add(carrier.GetInstanceID(), path);
        }

        // TMP reloads a face when adding glyphs. All of its Font,int calls are
        // routed here so dynamic atlases keep using the packaged TTF as well.
        public static FontEngineError LoadFontFace(Font font, int pointSize)
        {
            string path;
            return font != null && Paths.TryGetValue(font.GetInstanceID(), out path)
                ? FontEngine.LoadFontFace(path, pointSize)
                : FontEngine.LoadFontFace(font, pointSize);
        }
    }

    internal static class FontSupport
    {
        private const string CzechCharacters = "áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ„“–…";
        private static readonly Dictionary<string, TMP_FontAsset> Assets = new Dictionary<string, TMP_FontAsset>();
        private static readonly Dictionary<string, Material> Materials = new Dictionary<string, Material>();
        private static readonly HashSet<int> ReplacementIds = new HashSet<int>();
        private static readonly HashSet<string> Failures = new HashSet<string>();

        internal static void ReportFailure(string message)
        {
            if (Failures.Add(message)) Debug.LogWarning("KingOfTheCastleCZlocalMod font: " + message);
        }

        private static TMP_FontAsset GetFont(string directory, string filename)
        {
            TMP_FontAsset asset;
            if (Assets.TryGetValue(filename, out asset)) return asset;
            var path = Path.Combine(directory, filename);
            if (!File.Exists(path)) throw new FileNotFoundException("Missing packaged font", path);

            // The carrier is only a Unity object identity. FontLoader supplies
            // the actual TTF; no Windows font is used to draw the replacement.
            var carrier = new Font { name = filename };
            UnityEngine.Object.DontDestroyOnLoad(carrier);
            FontLoader.Register(carrier, path);
            asset = TMP_FontAsset.CreateFontAsset(carrier, 90, 9, GlyphRenderMode.SDFAA,
                2048, 2048, AtlasPopulationMode.Dynamic, true);
            if (asset == null) throw new InvalidOperationException("Cannot load " + filename);
            asset.name = "KingOfTheCastleCZlocalMod " + Path.GetFileNameWithoutExtension(filename);
            string unavailable;
            if (!asset.TryAddCharacters(CzechCharacters, out unavailable))
                throw new InvalidOperationException(filename + ": missing glyphs " + unavailable);
            UnityEngine.Object.DontDestroyOnLoad(asset);
            UnityEngine.Object.DontDestroyOnLoad(asset.material);
            foreach (var texture in asset.atlasTextures)
                if (texture != null) UnityEngine.Object.DontDestroyOnLoad(texture);
            Assets.Add(filename, asset);
            ReplacementIds.Add(asset.GetInstanceID());

            if (filename == "NotoSans-Regular.ttf")
                asset.fontWeightTable[7].regularTypeface = GetFont(directory, "NotoSans-Bold.ttf");
            if (filename == "MedievalSharp.ttf")
                asset.fallbackFontAssetTable = new List<TMP_FontAsset> { GetFont(directory, "NotoSans-Regular.ttf") };
            Debug.Log("KingOfTheCastleCZlocalMod: loaded " + filename + " with Czech glyphs.");
            return asset;
        }

        private static Material GetMaterial(Material original, TMP_FontAsset font)
        {
            if (original == null) return font.material;
            var key = original.GetInstanceID() + ":" + font.GetInstanceID();
            Material material;
            if (Materials.TryGetValue(key, out material)) return material;
            // Keep the game's colors, outlines, masking and shader keywords.
            // Only the atlas and its distance-field parameters change.
            material = new Material(original) { name = original.name + " Czech" };
            material.mainTexture = font.atlasTexture;
            SetFloat(material, "_TextureWidth", font.atlasWidth);
            SetFloat(material, "_TextureHeight", font.atlasHeight);
            SetFloat(material, "_GradientScale", font.atlasPadding + 1);
            SetFloat(material, "_WeightNormal", font.normalStyle);
            SetFloat(material, "_WeightBold", font.boldStyle);
            UnityEngine.Object.DontDestroyOnLoad(material);
            Materials.Add(key, material);
            return material;
        }

        private static void SetFloat(Material material, string property, float value)
        {
            if (material.HasProperty(property)) material.SetFloat(property, value);
        }

        internal static void Apply(TMP_Text text, string directory)
        {
            var original = text.font;
            if (original == null || ReplacementIds.Contains(original.GetInstanceID())) return;
            var replacement = GetFont(directory, FontSelection.Select(original.name));
            var material = GetMaterial(text.fontSharedMaterial, replacement);
            text.font = replacement;
            text.fontSharedMaterial = material;
        }
    }
}
