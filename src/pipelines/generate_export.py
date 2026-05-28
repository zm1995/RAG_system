"""阶段一：从 raw 数据源生成 export JSON。"""

import argparse
import sys

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from src.config import SOURCE_COZE, SOURCE_VIDEO, SOURCE_WEIXIN
from src.processors import CozeProcessor, VideoProcessor, WeixinProcessor

PROCESSORS = {
    SOURCE_COZE: CozeProcessor,
    SOURCE_WEIXIN: WeixinProcessor,
    SOURCE_VIDEO: VideoProcessor,
    "all": None,
}


def main():
    parser = argparse.ArgumentParser(description="生成 AI 助教 export JSON")
    parser.add_argument(
        "--source",
        choices=[SOURCE_COZE, SOURCE_WEIXIN, SOURCE_VIDEO, "all"],
        default="all",
    )
    parser.add_argument("--limit", type=int, default=None, help="每源最多处理文件数（调试用）")
    args = parser.parse_args()

    sources = [SOURCE_COZE, SOURCE_WEIXIN, SOURCE_VIDEO] if args.source == "all" else [args.source]

    for name in sources:
        print(f"\n{'=' * 50}")
        print(f"处理数据源: {name}")
        processor = PROCESSORS[name]()
        stats = processor.run(limit=args.limit)
        print(f"  待处理: {stats['total']}, 成功: {stats['ok']}, 失败: {stats['fail']}, 导出 JSON: {stats['exports']}")


if __name__ == "__main__":
    main()
