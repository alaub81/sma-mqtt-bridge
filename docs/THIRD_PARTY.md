# Third-party attribution

The original development foundation came from BMW-MQTT-Bridge. Its MIT copyright attribution is retained in the root [LICENSE](../LICENSE). The original source commit and transferred-file checksums remain in [BASELINE.md](BASELINE.md) and `baseline-manifest.json`. That manifest records the initial import, not the current filesystem.

The C++ diagnostic runtime, build scripts, duplicate Dockerfile and vendored JSON header were removed during the Python cleanup. Private originals remain read-only references and the removed public files remain recoverable in local Git history. No nlohmann/json code is used by the Python runtime or its image.

## Historical nlohmann/json notice

JSON for Modern C++, version 3.12.0: <https://github.com/nlohmann/json>.

Copyright (c) 2013-2025 Niels Lohmann.

MIT License:

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
