#nullable disable
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;

namespace Kotc.Czech
{
    // Pure text processing: the code checks can exercise this without Unity.
    public sealed class TextLocalizer
    {
        private sealed class Template { public Regex Pattern; public string Target; }
        private readonly IDictionary<string, string> translations;
        private readonly HashSet<string> translatedValues;
        private readonly List<Template> templates = new List<Template>();
        private readonly Dictionary<string, string> cache = new Dictionary<string, string>();
        private static readonly Regex Placeholder = new Regex(@"\{(\d+)\}");
        private static readonly Regex Tags = new Regex(@"(<[^>]+>)");
        private static readonly Regex Territories = new Regex(@"\b(?:the|The) (?:North|East|South|Coast|March|Capital)\b");
        private static readonly Regex Pronouns = new Regex(@"\b(he|she|they|He|She|They|HE|SHE|THEY)\b");
        private static readonly Regex RoleTitles = new Regex(@"\b(Lord Patrician|Lady Patrician|Noble Patrician|Expedition Soldier|Baroness|Barone|Countess|Conte|Kingdom|Success|Failure|success|failure)\b");
        private static readonly Regex DataDisplayNames = new Regex(@"\b(Cultists of the Undivided|Disciples of the Tenth|Barons' Barley of Bliss|Cabbage of Eastern Tranquillity|the Order of the Wilted Ring|the Swords of Emmeline|the Wings of Chyler|Sisterhood of Steel glide|the Republic of Kirth|a Zykerian black pearl|a rare Eastern herb, known as Sashara's Tears|a small vial of Tajorran frankincense|the pickled finger of an ice giant|the powdered tusk of a Greater Black Marchboar)\b");
        private static readonly Regex Terms = new Regex(@"\b(Meat and Two Breads|Footlongs|Footlong|END|Chiefs|CHIEFS|Counts|COUNTS|Grandees|GRANDEES|Patricians|PATRICIANS|Barons|BARONS|Spring|Summer|Autumn|Winter|Monarch|Nobles|Noble|Treasury|Authority|Stability|Defiance|Trade|Faith|Farming|Military|Heir|Ambition|Wealth|Raise|Lower|King|Queen|Prince|Princess|Lord|Lady|Duke|Duchess|Count|Chief|Grandee|Patrician|Baron|Chancellor|Spymaster|Treasurer|Marshal)\b");
        public int TemplateCount { get { return templates.Count; } }

        public TextLocalizer(IDictionary<string, string> values)
        {
            translations = values;
            translatedValues = new HashSet<string>(values.Values);
            foreach (var pair in values.OrderByDescending(p => p.Key.Length))
            {
                if (!Placeholder.IsMatch(pair.Key)) continue;
                // A template such as "{0} {1}" matches every sentence and is unsafe.
                if (Regex.Matches(Placeholder.Replace(pair.Key, ""), "[A-Za-z]").Count < 3) continue;
                var pattern = Regex.Escape(pair.Key);
                foreach (var id in Placeholder.Matches(pair.Key).Cast<Match>().Select(m => m.Groups[1].Value).Distinct())
                {
                    var escaped = Regex.Escape("{" + id + "}");
                    var first = pattern.IndexOf(escaped, StringComparison.Ordinal);
                    pattern = pattern.Substring(0, first) + "(?<p" + id + ">.+?)" + pattern.Substring(first + escaped.Length);
                    pattern = pattern.Replace(escaped, @"\k<p" + id + ">");
                }
                templates.Add(new Template { Pattern = new Regex("^" + pattern + "$", RegexOptions.Singleline, TimeSpan.FromMilliseconds(50)), Target = pair.Value });
            }
        }

        public string Localize(string value) { return Localize(value, 0); }
        private string Localize(string value, int depth)
        {
            if (String.IsNullOrEmpty(value) || depth > 32) return value;
            string result;
            if (translations.TryGetValue(value, out result)) return result;
            if (cache.TryGetValue(value, out result)) return result;
            var key = value.Trim();
            if (translatedValues.Contains(key)) return value;
            if (translations.TryGetValue(key, out result)) return Remember(value, PreserveWhitespace(value, result));
            foreach (var template in templates)
            {
                Match match;
                try { match = template.Pattern.Match(key); }
                catch (RegexMatchTimeoutException) { continue; }
                if (!match.Success) continue;
                result = Placeholder.Replace(template.Target, m => {
                    var captured = match.Groups["p" + m.Groups[1].Value].Value;
                    return captured.Length < key.Length ? Localize(captured, depth + 1) : captured;
                });
                return Remember(value, PreserveWhitespace(value, result));
            }
            var parts = Tags.Split(value);
            for (int i = 0; i < parts.Length; i += 2)
                parts[i] = Pronouns.Replace(Territories.Replace(Terms.Replace(RoleTitles.Replace(DataDisplayNames.Replace(parts[i], m => translations.TryGetValue(m.Value,out var name) ? name : m.Value), m => translations.TryGetValue(m.Value,out var role) ? role : m.Value), m => translations.TryGetValue(m.Value, out var target) ? target : m.Value), m => translations.TryGetValue(m.Value,out var territory) ? territory : m.Value), m => {
                    var key=m.Value.ToLowerInvariant();
                    if (!translations.TryGetValue(key,out var target)) return m.Value;
                    if (m.Value==m.Value.ToUpperInvariant()) return target.ToUpperInvariant();
                    return Char.IsUpper(m.Value[0]) ? Char.ToUpperInvariant(target[0])+target.Substring(1) : target;
                });
            return Remember(value, String.Concat(parts));
        }

        private static string PreserveWhitespace(string original, string target)
        {
            int begin = 0, end = original.Length;
            while (begin < end && Char.IsWhiteSpace(original[begin])) begin++;
            while (end > begin && Char.IsWhiteSpace(original[end - 1])) end--;
            return original.Substring(0, begin) + target + original.Substring(end);
        }

        private string Remember(string key, string value)
        {
            if (cache.Count >= 20000) cache.Clear();
            cache[key] = value;
            return value;
        }
    }
}
