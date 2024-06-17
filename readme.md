# `MLTマルチメディアフレームワーク`と`melt`と`Python`バインディング
## はじめに
先日`kdenlive`の[映像エフェクトレンダリングデモ一覧の記事](https://zenn.dev/ykesamaru/articles/35de0c41db36d1)を書いたわけですが、あれらのエフェクトは`kdenlive`などのノンリニア動画編集ソフトを使用しないと実現できないものなのでしょうか？つまりコマンドラインから編集はできないのでしょうか？

はい、映像編集もコマンドラインから可能です。

例えば画像編集ソフトである`GIMP`は高機能ですが、簡単な編集であれば`ImageMagick`で代用できますよね。
同じように、`kdenlive`や`Shotcut`のような高機能な映像編集ソフトを使わなくても、簡単なエフェクト処理であれば`Melt`というコマンドで行うことができます。

| GUI | CLI  |
|---|---|
| GIMP | ImageMagick |
| kdenlive | Melt |

また`ImageMagick`や`Melt`は必ずしもワンライナーで書かなくてはいけないという制限はありません。
好きなだけ複雑なスクリプトを書けるわけですが、先程例えに出した`ImageMagick`と`Melt`では、そのスクリプトに違いがあります。

どういうことでしょうか？

`ImageMagick`の場合、`convert`や`mogrify`などをシェルスクリプトの形にすれば複雑な編集が可能です。
`Melt`の場合も同様、シェルスクリプトに書くことができます。
しかし`Melt`の場合は`MLT XML`という、`XML`で記述するところに真骨頂があります。
そしてそのXMLファイル作成用のPythonバインディングが存在します。

応用範囲がものすごく広がりそうだと思いませんか？

今回の記事では、`Melt`の紹介はもとより、その背後の`MLTマルチメディアフレームワーク`の仕組みにも触れて、コマンドラインからの映像編集がどのようなものか、さらにPythonバインディングまで紹介したいと思います。

![元画像](https://raw.githubusercontent.com/yKesamaru/MLT_and_python/master/assets/example.png)
元画像

## MLTマルチメディアフレームワークとはなにか？
ノンリニア動画編集ソフトである`Shotcut`, `kdenlive`や`OpenShot`では背後に`MLTマルチメディアフレームワーク`が使われています。
`MLTマルチメディアフレームワーク`は、動画編集およびメディア処理のためのオープンソースフレームワークです。
メディアファイルの処理、エフェクトの適用、トランジションの追加、オーディオ処理などを定義出来ます。
動画編集ソフトウェアのバックエンドとして使用されていて、`Kdenlive`や`Shotcut`は、`MLTマルチメディアフレームワーク`を使用する代表的な動画編集ソフトウェアです[^1]。
[^1]: `Shotcut`は`MLT`と開発者が同じ人(Dan Dennedy)。

*MLTエンジン、MLTサービス、MLTプロデューサー、MLTコンシューマーなどのコンポーネント*から構成されます。

以下に、`MLTマルチメディアフレームワーク`のコンポーネントと構造要素の概念をそれぞれ示します。

### コンポーネント

| コンポーネント       | 説明                                                                                                      |
|----------------------|-----------------------------------------------------------------------------------------------------------|
| MLTエンジン          | メディア処理のコアとなるエンジン。メディアファイルの読み込み、エフェクトの適用、トランジションの処理を行う  |
| MLTサービス          | 各種エフェクトやフィルタを提供するプラグイン形式のサービス。`frei0r`、`movit`などのエフェクトサービス、`sox`などのフィルタサービス、`mix`などのトランジションサービスが存在します |
| MLTプロデューサー    | メディアファイルを読み込み、タイムライン上で再生するためのコンポーネント。ローカルからメディアファイルを読み込むファイルプロデューサー、ハードウェアデバイスからメディアを取り込むデバイスプロデューサー、ネットワークからメディアデータを取得するネットワークプロデューサーなどがあります                              |
| MLTコンシューマー    | レンダリング結果を出力するためのコンポーネント。ファイルに保存したり、リアルタイムプレビューを表示したりします。ファイルを出力、保存するファイルコンシューマー、処理結果をリアルタイムで画面に表示するスクリーンコンシューマー、処理結果をネットワークにストリーミングするストリームコンシューマーがあります。  |

### 構造要素

| 構造要素             | 説明                                                                                                      |
|----------------------|-----------------------------------------------------------------------------------------------------------|
| プロファイル      | プロジェクトの全体設定（解像度、フレームレート、カラースペースなど）を定義します。                                                            |
| プレイリスト      | 複数のメディアクリップを管理し、タイムライン上での再生順序を決定します。                                                                    |
| トラクター        | タイムライン管理を行い、複数のトラックやトランジションを含むコンポーネント                                                              |
| フィルター        | メディアデータに対してエフェクトやフィルタを適用するコンポーネント                                                                     |
| トランジション    | 異なるメディアクリップ間の切り替えをスムーズに行うためのコンポーネント                                                                 |

### どのように記述されるか
`MLT XML`として記述します。
このファイルには、プロジェクトの設定、使用するメディアファイル、適用するエフェクトやフィルタ、トラック構成などが記述されます。映像編集のレシピと考えて良さそうです。このレシピをもとに`MLTエンジン`が動作します。
#### `MLT XML`の例
```xml
<mlt>
  <!-- ビデオの解像度、フレームレート、カラー空間などの設定を定義。プロファイル部分。 -->
  <profile description="HD 1080p 25 fps" width="1920" height="1080" progressive="1" frame_rate_num="25" frame_rate_den="1" colorspace="709"/>

  <!-- メディアファイルを定義。MLTプロデューサー部分。 -->
  <producer id="producer0" in="0" out="250">
    <property name="resource">input_video.mp4</property>
    <property name="mlt_service">avformat</property>
  </producer>
  
  <!-- トラック（プレイリスト）を定義。プロデューサーをトラックに追加。プレイリスト部分。 -->
  <playlist id="playlist0">
    <entry producer="producer0"/>
  </playlist>
  
  <!-- エフェクト（フィルタ）を定義。ここでは、フェードインエフェクトを追加。MLTサービス部分 -->
  <filter id="filter0" mlt_service="frei0r.alphaatop" in="0" out="50">
    <property name="0">0.0=0;1.0=1</property>
  </filter>
  
  <!-- タイムラインを定義。トラックやトランジションを含む。トラクター部分。 -->
  <tractor id="tractor0">
    <track producer="playlist0"/>
    <transition mlt_service="mix" in="0" out="250"/>
  </tractor>
</mlt>
```


## `MLTマルチメディアフレームワーク`の使用例

`MLTマルチメディアフレームワーク`を使用して、動画編集を行いましょう。

### `Melt`のインストール
コマンドラインから動画編集を可能にする`Melt`をインストールします。
```bash
sudo apt install -y melt
```
```bash
以下のパッケージが新たにインストールされます:
  libebur128-1 liblept5 libmlt++7 libmlt-data libmlt7 libmovit8 libopencv-calib3d4.5d libopencv-contrib4.5d libopencv-dnn4.5d
  libopencv-features2d4.5d libopencv-flann4.5d libopencv-highgui4.5d libopencv-ml4.5d libopencv-objdetect4.5d libopencv-video4.5d librtaudio6
  libtesseract4 melt
```
`libmlt7`などが`MLT`関連のライブラリです。

それでは動作確認をしましょう。
```bash
melt sample.mp4 -filter frei0r.emboss -consumer avformat:output_video.gif r=10
```
- `-filter frei0r.emboss`
  - 入力ファイルに対してエフェクト処理をする
- `-consumer avformat`
  - `FFmpeg`の`avformat`ライブラリを使用して、出力ファイルを作成
- `r`
  - フレームレートを指定。`r=10`は10fps。
![](https://raw.githubusercontent.com/yKesamaru/MLT_and_python/master/assets/output_video.gif)

動作確認終了です。

#### `Melt`で使用可能なフィルタサービス（エフェクト）
`Melt`で使用できるエフェクトは以下のようにして取得可能です。
```bash
melt -query "filters"
---
filters:
  - avcolour_space
  - avcolor_space
  - avdeinterlace
  - swscale
  - avfilter.abench
  - avfilter.acompressor
  - avfilter.acontrast
  - avfilter.acue
（後略）
```
このフィルタにはオーディオフィルタも含まれますが、**450種類**(！)くらいのフィルタが出力されます。
もし個々のフィルタの設定を知りたい場合は`-query`引数を用います。
```bash
# melt -query "filter=<フィルタ名>
melt -query "filter=frei0r.emboss"
---
schema_version: 0.3
title: emboss
version: 0.1
identifier: frei0r.emboss
description: Creates embossed relief image of source image
creator: Janne Liljeblad
type: filter
tags:
  - Video
parameters:
  - identifier: 0
    title: azimuth
    description: Light direction
    type: float
    minimum: 0
    maximum: 1
    default: 0.375
    mutable: yes
    widget: spinner
  - identifier: 1
    title: elevation
    description: Background lightness
    type: float
    minimum: 0
    maximum: 1
    default: 0.333333
    mutable: yes
    widget: spinner
  - identifier: 2
    title: width45
    description: Bump height
    type: float
    minimum: 0
    maximum: 1
    default: 0.25
    mutable: yes
    widget: spinner
...
```
これをみるとデフォルト値がいくつなのか、設定値の範囲はどれくらいかを確認できます。
この出力結果をみると、変更可能なパラメータは`azimuth, elevation, width45`だとわかります。`azimuth`は光の方向、`elevation`は背景の明るさ、`width45`はバンプの高さを表します。そしてこれらには個別の`identifier`が割り振られています。例えば`azimuth`なら`identifier`は`0`です。そして各設定値は`:`でつなげて指定します。
たとえば先程の`emboss`フィルタではデフォルト値が使われたのでした。この値を以下のように変化させるとどうなるでしょうか。
```bash
melt sample.mp4 -filter frei0r.emboss:0=0.0:1=0.9:2=0.0 -consumer avformat:output_3.gif r=5
```

入力が静止画の場合、`in`と`out`を指定します。`out`がフレーム数となります。
```bash
melt example.png in=0 out=10 -filter oldfilm -consumer avformat:output_oldfilm.gif
```
![](https://raw.githubusercontent.com/yKesamaru/MLT_and_python/master/assets/output_oldfilm.gif)

***※ 書式に間違いはないように思えますが、わたしの環境では`-filter`の引数が反映されませんでした。これは`emboss`だけでなく、`oldfilm`においても同様でした。後述のMLT XML使用時は機能しました***

```bash
melt example.png in=0 out=10 -filter oldfilm:delta=400:brightnessdelta_up=100:brightnessdelta_down=100 -consumer avformat:oldfilm02.gif
```
![](https://raw.githubusercontent.com/yKesamaru/MLT_and_python/master/assets/oldfilm02.gif)

詳細は`man melt`にて確認できます。また付加情報は[Melt Documentation](https://www.mltframework.org/docs/melt/)にあります。試してはいませんがドキュメンテーションによると2トラック以上のエフェクトの追加など複雑なことが可能なようです。
ただし、ドキュメンテーションにあるように
- コマンドライン解析時のエラーチェックが弱いこと
- 複雑な処理には複雑なコマンドラインを構築しなければならないこと（非現実的）

とあります。

では、複雑なコマンドライン構築を避けて、なおかつ思い通りの映像エフェクトを実現できないものでしょうか？

それを解決するのが次に説明する`MLT XML`の仕組み(`MLT Multimedia Framework`)とそのバインディングである`python3-mlt`です。


#### MLTのインストール(`python3-mlt`)
というわけで、`MLT Multimedia Framework`を利用するためにパイソンバインディングをインストールしていきましょう。
※  `melt`をインストールしていない場合、MLTのPythonバインディングである`python3-mlt`をインストールすると必要なライブラリ群(`libmlt7`など)が一緒にインストールされます。
- `libmlt7`: MLTライブラリの主要な部分
- `libmlt++7`: MLTライブラリのC++バインディング
- `libmlt-data`: MLTライブラリに関連するデータ
- その他、多数の依存パッケージ（例：`libavcodec60`、`libavformat60`、`libavutil58`など）、FFmpegなどに必要なライブラリ

リポジトリは`Ubuntu 22.04 LTS`の`universe`リポジトリになります。

はじめ、普段使用しているシステムに`venv`による仮想環境を作り、そこで`MLT`を試そうとしましたが、システムにライブラリをインストールしないといけないことがわかりました。

そこでここでは`Gnome Boxes`にインストールした`Ubuntu 22.04 LTS`に`python3-mlt`をインストールします。
`python3-mlt`自体も`universe`セクションにあります。
```bash
# Gnome BoxesのUbuntu 22.04にインストール
sudo add-apt-repository universe
sudo apt update && apt upgrade -y
sudo apt install python3-mlt
```

インストールが完了したら、以下のPythonスクリプトを実行して、MLTが正しくインストールされているか確認します。

```bash
$ python3Python 3.10.12 (main, Nov 20 2023, 15:14:05) [GCC 11.4.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import mlt7
>>> mlt_version = mlt7.Factory().init()
No LADSPA plugins were found!
Check your LADSPA_PATH environment variable.
>>> print("MLT Version:", mlt_version)
MLT Version: <mlt7.Repository; proxy of <Swig Object of type 'Mlt::Repository *' at 0x7b9040195890> >
>>> 
```
このように表示されればインストールは完了です。

### PythonでMLTを使用して動画にエフェクトを追加
まず、`lxml`ライブラリを使用してMLT XMLを生成し、それを使って動画にエフェクトを適用します。
前もって`pip`でインストールをしておきましょう。
```bash
# pipなどのアップグレード
pip install -U pip wheel setuptools
pip install lxml
```
それではPythonをつかって`MLT XMLファイル`を作成します。

下記のPythonスクリプトは下記のコマンドラインと同様の動作を定義する`MLT XMLファイル`を作成するものです。
```bash
melt example.png in=0 out=10 -filter oldfilm:delta=400:brightnessdelta_up=100:brightnessdelta_down=100 -consumer avformat:oldfilm02.gif
```

```python
from lxml import etree


def create_mlt_xml_with_oldfilm(input_image, output_xml):
    # MLT XMLのルート要素を作成
    mlt = etree.Element('mlt', version="7.4.0")

    # プロファイルを追加
    profile = etree.SubElement(mlt, 'profile', {
        'description': 'NTSC 720x480 10fps',  # プロファイルの説明
        'width': '720',  # 横幅720px
        'height': '480',  # 縦幅480px
        'progressive': '1',  # プログレッシブスキャン
        'frame_rate_num': '10',  # フレームレートの分子
        'frame_rate_den': '1',  # フレームレートの分母
        'colorspace': '601'  # カラースペース（オプション）
    })

    # プロデューサーを追加
    producer = etree.SubElement(mlt, 'producer', id="producer0")
    property_element = etree.SubElement(producer, 'property', name="resource")
    property_element.text = input_image
    property_element = etree.SubElement(producer, 'property', name="mlt_service")
    property_element.text = 'qimage'

    # プレイリストを追加
    playlist = etree.SubElement(mlt, 'playlist', id="playlist0")
    entry = etree.SubElement(playlist, 'entry', producer="producer0", **{"in": "0", "out": "10"})

    # oldfilmエフェクトを追加
    filter_element = etree.SubElement(playlist, 'filter', id="filter0")
    filter_element.set('mlt_service', 'oldfilm')
    filter_element.set('in', '0')
    filter_element.set('out', '10')
    
    param_delta = etree.SubElement(filter_element, 'property', name="delta")
    param_delta.text = '400'
    param_brightness_up = etree.SubElement(filter_element, 'property', name="brightnessdelta_up")
    param_brightness_up.text = '100'
    param_brightness_down = etree.SubElement(filter_element, 'property', name="brightnessdelta_down")
    param_brightness_down.text = '100'

    # タイムラインを追加
    tractor = etree.SubElement(mlt, 'tractor', id="tractor0")
    track = etree.SubElement(tractor, 'track', producer="playlist0")
    transition = etree.SubElement(tractor, 'transition', {
        'mlt_service': 'mix',
        'in': '0',
        'out': '10'
    })

    # XMLツリーをファイルに保存
    tree = etree.ElementTree(mlt)
    tree.write(output_xml, pretty_print=True, xml_declaration=True, encoding='UTF-8')

if __name__ == "__main__":
    # 使用例
    create_mlt_xml_with_oldfilm("assets/example.png", "output_with_oldfilm.mlt")
```

このスクリプトを実行した結果が以下になります。
```xml
<?xml version='1.0' encoding='UTF-8'?>
<mlt version="7.4.0">
  <profile description="NTSC 720x480 10fps" width="720" height="480" progressive="1" frame_rate_num="10" frame_rate_den="1" colorspace="601"/>
  <producer id="producer0">
    <property name="resource">assets/example.png</property>
    <property name="mlt_service">qimage</property>
  </producer>
  <playlist id="playlist0">
    <entry producer="producer0" in="0" out="10"/>
    <filter id="filter0" mlt_service="oldfilm" in="0" out="10">
      <property name="delta">400</property>
      <property name="brightnessdelta_up">100</property>
      <property name="brightnessdelta_down">100</property>
    </filter>
  </playlist>
  <tractor id="tractor0">
    <track producer="playlist0"/>
    <transition mlt_service="mix" in="0" out="10"/>
  </tractor>
</mlt>
```

このファイルが`MLT XMLファイル`です。このファイルがレシピとなります。
ではこのレシピをもとにファイルの変換を行いましょう。
```bash
melt output_with_oldfilm.mlt -consumer avformat:output_oldfilm.gif
```

出来上がったファイルが以下になります。`mlt`コマンドでは引数が動作しないバグ？がありましたが、こちらはきちんと設定値が反映されているようです。
![](https://raw.githubusercontent.com/yKesamaru/MLT_and_python/master/assets/output_oldfilm_from_xml.gif)


## 最後に
今回は例を示しただけですので、もしかしたら「せっかく`MLT XMLファイル`を作成しても`melt`コマンドとできることが同じなら`melt`コマンドだけで良くない？」と思われる方もいらっしゃると思います。
ではなぜ`MLT XML`の仕組みがあるのかと言えば、もっとずっと複雑な指示が記載できるからです。たとえば`kdenlive`や`Shotcut`などでは内部で`MLT XML`を利用しています。複数トラックのコンポジションやトランジション、映像だけでなくオーディオのエフェクト、どのようなファイル形式で書き出すかなど、ありとあらゆることができるようになります。
逆に今回の例のように簡単なものであれば`melt`コマンド単体のほうが簡単です。
あるいはPythonスクリプトで`MLT XML`ファイルを作成できるようにしておくことで、再利用性が上がりますし、複数のファイルを一度に処理できたり、条件分岐したりと汎用性をもたせることもできます。利用範囲次第、ということですね。

以上です。ありがとうございました。

## 参考文献
- [Media Lovin' Toolkit: Wikipedia](https://en.wikipedia.org/wiki/Media_Lovin%27_Toolkit)
- [MLT Documentation](https://www.mltframework.org/docs/)
  - [Melt](https://www.mltframework.org/docs/melt/)
  - [MLT Multimedia Framework](https://www.mltframework.org/)
- [MLT Framework(GitHub)](https://github.com/mltframework)


---

## 補足
本文に入れるには冗長な情報を以下に記述します。
### MLTマルチメディアフレームワークの歴史
> 1. **2002年 - プロジェクト開始**
>    - MLT (Media Lovin' Toolkit) プロジェクトは、Dan Dennedyによって開始されました。彼は当時、放送業界での使用を目的としたメディア編集フレームワークを開発していました。
> 2. **2003年 - 初期開発とリリース**
>    - 初期バージョンが公開され、基本的なメディア処理機能が実装されました。MLTは、当初からモジュール化されたプラグインアーキテクチャを持ち、さまざまなメディア形式とエフェクトをサポートしました。
> 3. **2005年 - Kdenliveとの統合**
>    - Kdenlive（KDE Non-Linear Video Editor）との統合が進みました。これにより、KdenliveはMLTをバックエンドとして使用することで、より強力な動画編集機能を提供できるようになりました。
> 4. **2007年 - プロジェクトの成長**
>    - MLTは、より多くのエフェクト、トランジション、フィルタをサポートするように成長しました。また、コミュニティの貢献が増え、フレームワークの機能が拡張されました。
> 5. **2010年 - OpenShotとの連携**
>    - OpenShot Video EditorもMLTをバックエンドとして採用しました。これにより、OpenShotも多くのMLTの機能を利用できるようになり、ユーザーに対して強力な動画編集機能を提供できるようになりました。
> 6. **2012年 - MLTの成熟**
>    - MLTは、バージョン0.8をリリースし、安定性とパフォーマンスが大幅に向上しました。また、クロスプラットフォーム対応が強化され、WindowsやmacOSでも利用できるようになりました。
> 7. **2015年 - 新しいエフェクトとフィルタの追加**
>    - コミュニティの継続的な貢献により、新しいエフェクトやフィルタが追加されました。特に、映像とオーディオの処理機能が強化され、プロフェッショナルな編集作業にも対応できるようになりました。
> 8. **2020年 - 現在**
>    - MLTは、引き続き活発に開発されています。最新バージョンでは、より多くのメディア形式のサポート、高度なエフェクト、リアルタイムプレビュー機能などが強化されています。また、KdenliveやShotcutなどの動画編集ソフトウェアのバックエンドとして広く使用されています。

### MLT、GStreamer、FFmpegの関係
| 技術       | 説明                                                                                                  |
|------------|-------------------------------------------------------------------------------------------------------|
| MLT        | 非線形ビデオ編集エンジン。複数のオーディオおよびビデオトラックを管理し、エフェクトやトランジションを適用。           |
| GStreamer  | マルチメディアフレームワーク。リアルタイム処理やストリーミングに強みがあり、MLTのプラグインとして利用されることがある。 |
| FFmpeg     | マルチメディア処理ライブラリ。エンコード/デコード、フィルタリング、エフェクトの適用においてMLTで広く利用される。      |

### MLTの主な特徴
| 特徴                  | 説明                                                                 |
|-----------------------|----------------------------------------------------------------------|
| モジュール化          | プラグインを通じて機能を拡張できる。                                           |
| クロスプラットフォーム | Linux、Windows、macOSで動作。                                          |
| オープンソース        | ソースコードが公開されており、自由に利用および改良が可能。                         |
| 他のライブラリとの統合 | FFmpegやGStreamerと統合し、広範なメディアフォーマットをサポート。                  |

### MLTを使用しているアプリケーション
| アプリケーション | プラットフォーム                     | 説明                                                                     |
|------------------|----------------------------------|------------------------------------------------------------------------|
| Kdenlive         | Linux, Windows, macOS            | KDEプロジェクトの一部であり、強力な非線形ビデオ編集ソフトウェア。                                    |
| Shotcut          | Linux, Windows, macOS            | クロスプラットフォームのオープンソース動画編集ソフトウェア。                                               |
| Flowblade        | Linux                            | マルチトラック非線形動画編集ソフトウェア。                                                   |
| OpenShot         | Linux, Windows, macOS            | 使いやすさに重点を置いたオープンソース動画編集ソフトウェア。                                           |

### 非線形ビデオ編集エンジンの機能
| 機能              | 説明                                                                                   |
|-------------------|--------------------------------------------------------------------------------------|
| マルチトラック編集 | 複数のビデオおよびオーディオトラックを扱い、タイムライン上で自由に配置して編集できる。                          |
| リアルタイムプレビュー | エフェクトやトランジションをリアルタイムでプレビューしながら編集できる。                                            |
| エフェクトとフィルタ  | 映像や音声に対してさまざまなエフェクトやフィルタを適用できる。                                                 |
| トランジション       | 異なるクリップ間のシームレスな切り替えを提供するトランジション効果をサポート。                                          |
| レンダリング       | 最終的な編集結果をファイルとして出力するためのレンダリング機能を提供。                                              |


