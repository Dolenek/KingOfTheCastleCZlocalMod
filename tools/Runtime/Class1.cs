using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using Newtonsoft.Json;
using TMPro;
using UnityEngine;

namespace Kotc.Czech
{
    public static class Runtime
    {
        private static readonly object Gate = new object();
        private static TextLocalizer localizer;
        private static readonly HashSet<string> missing = new HashSet<string>();
        private static string modDir;

        private static void Load()
        {
            if (localizer != null) return;
            lock (Gate)
            {
                if (localizer != null) return;
                try
                {
                    modDir = Path.Combine(Path.GetDirectoryName(Application.dataPath), "KingOfTheCastleCZlocalMod");
                    var translations = JsonConvert.DeserializeObject<Dictionary<string, string>>(File.ReadAllText(Path.Combine(modDir, "translations.json")));
                    localizer = new TextLocalizer(translations);
                    Debug.Log("KingOfTheCastleCZlocalMod: loaded " + translations.Count + " translations and " + localizer.TemplateCount + " dynamic UI templates.");
                }
                catch (Exception e) { localizer = new TextLocalizer(new Dictionary<string, string>()); Debug.LogWarning("KingOfTheCastleCZlocalMod: " + e.Message); }
            }
        }

        public static string Localize(string value)
        {
            if (String.IsNullOrEmpty(value)) return value;
            try
            {
                Load();
                var result = localizer.Localize(value);
                var key = value.Trim();
                if (result == value && key.Length > 15 && Regex.IsMatch(key, @"\b(the|your|you|with|have|has|will|are|this|that)\b", RegexOptions.IgnoreCase) && missing.Count < 10000 && missing.Add(key))
                    File.AppendAllText(Path.Combine(modDir, "unmatched-ui.jsonl"), JsonConvert.SerializeObject(key) + "\n");
                return result;
            }
            catch { return value; }
        }

        private static bool IsUserInput(TMP_Text text)
        {
            var field = text.GetComponentInParent<TMP_InputField>();
            return field != null && field.textComponent == text;
        }

        public static string LocalizeForText(TMP_Text text, string value)
        {
            try { return IsUserInput(text) ? value : Localize(value); }
            catch { return value; }
        }

        public static void EnsureFont(TMP_Text text)
        {
            try
            {
                var translated = LocalizeForText(text, text.text);
                if (translated != text.text) text.text = translated;
                Load();
                FontSupport.Apply(text, Path.Combine(modDir, "fonts"));
            }
            catch (Exception e)
            {
                FontSupport.ReportFailure(e.Message);
            }
        }
    }
}
