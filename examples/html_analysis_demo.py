#!/usr/bin/env python3
"""
HTML解析デモンストレーション

このスクリプトは、CodeXrayのHTML解析機能を実際に使用する例を示します。
comprehensive_sample.htmlファイルを解析し、HTML要素の抽出、分類、階層構造の分析を行います。
"""

import asyncio
from pathlib import Path
from typing import Any

# CodeXrayのインポート
try:
    from codexray.core.analysis_engine import get_analysis_engine
    from codexray.formatters.html_formatter import HtmlFormatter
    from codexray.languages.html_plugin import HtmlPlugin
except ImportError as e:
    print(f"エラー: CodeXrayがインストールされていません: {e}")
    print("以下のコマンドでインストールしてください:")
    print("uv add 'codexray[html]'")
    exit(1)


class HtmlAnalysisDemo:
    """HTML解析デモクラス"""

    def __init__(self):
        self.engine = None
        self.html_plugin = HtmlPlugin()
        self.formatter = HtmlFormatter()
        self.sample_file = Path(__file__).parent / "comprehensive_sample.html"

    async def initialize(self):
        """解析エンジンの初期化"""
        print("🔧 CodeXray エンジンを初期化中...")
        self.engine = await get_analysis_engine()
        print("✅ 初期化完了")

    def check_sample_file(self) -> bool:
        """サンプルファイルの存在確認"""
        if not self.sample_file.exists():
            print(f"❌ サンプルファイルが見つかりません: {self.sample_file}")
            print("comprehensive_sample.htmlファイルを作成してください。")
            return False
        return True

    async def analyze_html_structure(self) -> dict[str, Any]:
        """HTML構造の解析"""
        print(f"\n📊 HTML構造解析: {self.sample_file.name}")
        print("=" * 60)

        try:
            # ファイルを解析
            result = await self.engine.analyze_file(str(self.sample_file))

            # 基本統計情報
            print(f"📄 ファイル: {result.file_path}")
            print(f"🔤 言語: {result.language}")
            print(f"📏 総行数: {result.metrics.lines_total}")
            print(f"💻 コード行数: {result.metrics.lines_code}")
            print(f"📝 コメント行数: {result.metrics.lines_comment}")
            print(f"⚪ 空行数: {result.metrics.lines_blank}")
            print(f"🧩 総要素数: {result.metrics.elements.total}")

            return result.to_dict()

        except Exception as e:
            print(f"❌ 解析エラー: {e}")
            return {}

    def analyze_element_classification(self, elements: list[dict[str, Any]]):
        """要素分類の分析"""
        print("\n🏷️ HTML要素分類分析")
        print("=" * 60)

        # 要素をタイプ別に分類
        classification = {}
        tag_counts = {}

        for element in elements:
            if element.get("element_type") == "html_element":
                # 要素クラス別の集計
                element_class = element.get("element_class", "unknown")
                if element_class not in classification:
                    classification[element_class] = []
                classification[element_class].append(element)

                # タグ名別の集計
                tag_name = element.get("tag_name", "unknown")
                tag_counts[tag_name] = tag_counts.get(tag_name, 0) + 1

        # 分類結果の表示
        print("📋 要素クラス別統計:")
        for class_name, class_elements in sorted(classification.items()):
            print(f"  {class_name}: {len(class_elements)}個")

            # 各クラスの代表的なタグを表示
            tags_in_class = {elem.get("tag_name", "") for elem in class_elements}
            sample_tags = sorted(tags_in_class)[:5]  # 最初の5個
            if sample_tags:
                print(f"    例: {', '.join(sample_tags)}")

        print("\n🏷️ 使用されているHTMLタグ (上位10個):")
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        for tag, count in sorted_tags[:10]:
            print(f"  <{tag}>: {count}回")

        return classification, tag_counts

    def analyze_hierarchy(self, elements: list[dict[str, Any]]):
        """階層構造の分析"""
        print("\n🌳 HTML階層構造分析")
        print("=" * 60)

        # ルート要素を見つける
        root_elements = []
        nested_elements = []

        for element in elements:
            if element.get("element_type") == "html_element":
                if element.get("parent") is None:
                    root_elements.append(element)
                else:
                    nested_elements.append(element)

        print(f"🌱 ルート要素: {len(root_elements)}個")
        print(f"🌿 ネストされた要素: {len(nested_elements)}個")

        # 主要なセクション要素を表示
        semantic_elements = [
            "html",
            "head",
            "body",
            "header",
            "nav",
            "main",
            "section",
            "article",
            "aside",
            "footer",
        ]
        found_semantic = []

        for element in elements:
            if element.get("element_type") == "html_element":
                tag_name = element.get("tag_name", "")
                if tag_name in semantic_elements and tag_name not in found_semantic:
                    found_semantic.append(tag_name)
                    start_line = element.get("start_line", "N/A")
                    end_line = element.get("end_line", "N/A")
                    print(f"  📍 <{tag_name}>: {start_line}-{end_line}行")

    def analyze_attributes(self, elements: list[dict[str, Any]]):
        """属性の分析"""
        print("\n🔧 HTML属性分析")
        print("=" * 60)

        all_attributes = {}
        class_values = set()
        id_values = set()

        for element in elements:
            if element.get("element_type") == "html_element":
                attributes = element.get("attributes", {})

                for attr_name, attr_value in attributes.items():
                    if attr_name not in all_attributes:
                        all_attributes[attr_name] = 0
                    all_attributes[attr_name] += 1

                    # class属性の値を収集
                    if attr_name == "class" and attr_value:
                        class_values.update(attr_value.split())

                    # id属性の値を収集
                    if attr_name == "id" and attr_value:
                        id_values.add(attr_value)

        # 属性使用頻度の表示
        print("📊 属性使用頻度 (上位10個):")
        sorted_attrs = sorted(all_attributes.items(), key=lambda x: x[1], reverse=True)
        for attr, count in sorted_attrs[:10]:
            print(f"  {attr}: {count}回")

        print(f"\n🎨 CSSクラス数: {len(class_values)}個")
        if class_values:
            sample_classes = sorted(class_values)[:10]
            print(f"  例: {', '.join(sample_classes)}")

        print(f"\n🆔 ID数: {len(id_values)}個")
        if id_values:
            sample_ids = sorted(id_values)[:5]
            print(f"  例: {', '.join(sample_ids)}")

    def demonstrate_html_formatter(self, analysis_result: dict[str, Any]):
        """HTMLフォーマッターのデモンストレーション"""
        print("\n📋 HTMLフォーマッター出力例")
        print("=" * 60)

        try:
            # フォーマッターを使用してテーブル形式で出力
            formatted_output = self.formatter.format_elements(
                analysis_result.get("elements", []), format_type="html"
            )

            # 出力の一部を表示（長すぎる場合は切り詰め）
            lines = formatted_output.split("\n")
            if len(lines) > 30:
                print("\n".join(lines[:25]))
                print(f"... (残り{len(lines) - 25}行)")
            else:
                print(formatted_output)

        except Exception as e:
            print(f"❌ フォーマッターエラー: {e}")

    async def run_demo(self):
        """デモの実行"""
        print("🌳 CodeXray HTML解析デモ")
        print("=" * 60)

        # 初期化
        await self.initialize()

        # サンプルファイルの確認
        if not self.check_sample_file():
            return

        # HTML構造解析
        analysis_result = await self.analyze_html_structure()
        if not analysis_result:
            return

        elements = analysis_result.get("elements", [])
        if not elements:
            print("❌ HTML要素が見つかりませんでした")
            return

        # 各種分析の実行
        self.analyze_element_classification(elements)
        self.analyze_hierarchy(elements)
        self.analyze_attributes(elements)
        self.demonstrate_html_formatter(analysis_result)

        print("\n✅ HTML解析デモ完了!")
        print(f"📊 解析された要素数: {len(elements)}")
        print("📄 詳細な解析結果は上記をご確認ください。")


async def main():
    """メイン関数"""
    demo = HtmlAnalysisDemo()
    await demo.run_demo()


if __name__ == "__main__":
    # 非同期実行
    asyncio.run(main())
