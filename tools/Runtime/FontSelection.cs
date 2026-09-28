using System;

namespace Kotc.Czech
{
    public static class FontSelection
    {
        // Filenames of the unmodified, OFL-licensed files in fonts/.
        public static string Select(string name)
        {
            if (name.IndexOf("Germania", StringComparison.OrdinalIgnoreCase) >= 0)
                return "MedievalSharp.ttf";
            return name.IndexOf("Bold", StringComparison.OrdinalIgnoreCase) >= 0
                ? "NotoSans-Bold.ttf" : "NotoSans-Regular.ttf";
        }
    }
}
