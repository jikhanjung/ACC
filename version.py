"""
ACC Version Information
Single Source of Truth for version management
"""

try:
    import semver

    __version__ = "0.0.5"

    # semver 라이브러리를 사용해 안전하게 파싱
    _ver = semver.VersionInfo.parse(__version__)
    __version_info__ = (_ver.major, _ver.minor, _ver.patch)
except ImportError:
    # semver가 없을 경우 fallback
    __version__ = "0.0.5"
    __version_info__ = (0, 0, 5)

__app_name__ = "ACC"
__author__ = "jikhanjung"
__description__ = "Area Affinity in Concentric Circles - Hierarchical cluster visualization"
__url__ = "https://github.com/jikhanjung/ACC"
