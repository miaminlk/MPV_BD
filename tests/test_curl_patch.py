"""Offline regression checks for curl's OpenSSL feature-detection patch."""

from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


PATCH = Path(__file__).resolve().parents[1] / "dependency-patches/curl-0002-check-asn1-string-api.patch"
# curl's upstream wrapper after ASN1_STRING_get_length was namespaced.
UPSTREAM_WRAPPER = """\
#if 1
typedef unsigned long sslerr_t;
#endif
#define ossl_valsize_t numcert_t

#if OPENSSL_VERSION_NUMBER >= 0x40100000L
#define ossl_ASN1_STRING_get_length ASN1_STRING_get_length
#else
static size_t ossl_ASN1_STRING_get_length(const ASN1_STRING *str)
{
   const int length = ASN1_STRING_length(str);
   return length >= 0 ? (size_t)length : 0;
}
#endif
"""


class CurlPatchTests(unittest.TestCase):
    def test_full_blob_ids_for_partial_clones(self):
        indexes = re.findall(r"^index (\S+)\.\.(\S+) 100644$", PATCH.read_text(), re.MULTILINE)
        self.assertEqual(len(indexes), 3)
        for before, after in indexes:
            self.assertRegex(before, r"^[0-9a-f]{40}$")
            self.assertRegex(after, r"^[0-9a-f]{40}$")

    @unittest.skipUnless(shutil.which("cc") and shutil.which("git"), "requires a C compiler and Git")
    def test_namespaced_wrapper_with_and_without_api(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "lib/vtls/openssl.c"
            source.parent.mkdir(parents=True)
            source.write_text(UPSTREAM_WRAPPER)
            subprocess.run(
                ["git", "apply", "--include=lib/vtls/openssl.c", str(PATCH)],
                cwd=root, check=True, capture_output=True, text=True,
            )
            wrapper = source.read_text()
            for has_api, version in ((False, "0x40100000L"), (True, "0x40100000L"), (True, "0x30000000L")):
                with self.subTest(has_api=has_api, version=version):
                    preamble = """\
#include <stddef.h>
#include <stdint.h>
typedef struct { int length; size_t api_length; } ASN1_STRING;
#define ASN1_STRING_length(s) ((s)->length)
""" + f"#define OPENSSL_VERSION_NUMBER {version}\n"
                    if has_api:
                        preamble += """\
#define HAVE_ASN1_STRING_GET_LENGTH 1
static size_t ASN1_STRING_get_length(const ASN1_STRING *s)
{
    return s->api_length;
}
"""
                    expected = "SIZE_MAX / 4" if has_api else "17"
                    negative_expected = "SIZE_MAX / 4" if has_api else "0"
                    program = preamble + wrapper + f"""
int main(void)
{{
    ASN1_STRING positive = {{17, SIZE_MAX / 4}};
    ASN1_STRING negative = {{-1, SIZE_MAX / 4}};
    return ossl_ASN1_STRING_get_length(&positive) != {expected} ||
           ossl_ASN1_STRING_get_length(&negative) != {negative_expected};
}}
"""
                    fixture = root / "wrapper.c"
                    executable = root / "wrapper"
                    fixture.write_text(program)
                    subprocess.run(
                        ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", str(fixture), "-o", str(executable)],
                        check=True, capture_output=True, text=True,
                    )
                    subprocess.run([str(executable)], check=True)


if __name__ == "__main__":
    unittest.main()
