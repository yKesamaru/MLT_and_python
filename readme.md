# `MLTマルチメディアフレームワーク`と`Python`
## はじめに
ノンリニア動画編集ソフトである`Shotcut`, `kdenlive`や`OpenShot`では背後に`MLTマルチメディアフレームワーク`が使われています。
後述しますが、動画編集の定義は`MLT XML`によって**文字列として**定義されます。
これはすなわち、**`Python`などで編集したり実行させたりが可能**だということを意味します。

この記事では`MLTマルチメディアフレームワーク`についての簡単な紹介と、その仕組みを通じてエフェクトの自動化を試みます。

## MLTマルチメディアフレームワークとはなにか？
MLTフレームワークは、動画編集およびメディア処理のためのオープンソースフレームワークです。
メディアファイルの処理、エフェクトの適用、トランジションの追加、オーディオ処理などを定義出来ます。
動画編集ソフトウェアのバックエンドとして使用されていて、`Kdenlive`や`Shotcut`は、MLTフレームワークを使用する代表的な動画編集ソフトウェアです[^1]。
[^1]: `Shotcut`は`MLT`と開発者が同じ人。

*MLTエンジン、MLTサービス、MLTプロデューサー、MLTコンシューマーなどのコンポーネント*から構成されます。

以下に、MLTフレームワークのコンポーネントと構造要素の概念をそれぞれ示します。

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
| トラクター        | タイムライン管理を行い、複数のトラックやトランジションを含むコンポーネントです。                                                              |
| フィルター        | メディアデータに対してエフェクトやフィルタを適用するコンポーネントです。                                                                     |
| トランジション    | 異なるメディアクリップ間の切り替えをスムーズに行うためのコンポーネントです。                                                                 |

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


### MLTフレームワークの使用例

MLTフレームワークを使用して、Pythonから動画編集を行う例を以下に示します。

#### インストール
##### MLTのインストール
MLT自体(`libmlt7`など)は`Ubuntu 22.04 LTS`の`universe`リポジトリにも存在します。
これらはMLTのPythonバインディングである`python3-mlt`をインストールすると自動的にインストールされます。

`Gnome Boxes`にインストールした`Ubuntu 24.04 LTS`に`python3-mlt`をインストールします。
`python3-mlt`自体も`universe`セクションにあります。
```bash
# Gnome BoxesのUbuntu 24.04にインストール
sudo add-apt-repository universe
sudo apt update && apt upgrade -y
sudo apt install python3-mlt
```

```bash
$ sudo apt install python3-mlt
パッケージリストを読み込んでいます... 完了
依存関係ツリーを作成しています... 完了        
状態情報を読み取っています... 完了        
以下の追加パッケージがインストールされます:
  gdal-data gdal-plugins i965-va-driver intel-media-va-driver libaacs0 libaec0 libarmadillo12 libarpack2t64 libass9 libavcodec60 libavdevice60 libavfilter9 libavformat60 libavutil58 libbdplus0 libblas3 libblosc1 libbluray2
（中略）
libpostproc57 libpq5
  libproj25 libqhull-r8.0 libqt5opengl5t64 libqt5test5t64 librabbitmq4 librav1e0 librist4 librtaudio6 librttopo1 librubberband2 libsdl1.2debian libsdl2-2.0-0 libserd-0-0 libshine3 libsnappy1v5 libsndio7.0 libsocket++1
  libsodium23 libsord-0-0 libsox-fmt-alsa libsox-fmt-base libsox3 libsoxr0 libspatialite8t64 libsphinxbase3t64 libsratom-0-0 libsrt1.5-gnutls libssh-gcrypt-4 libsuperlu6 libsvtav1enc1d1 libswresample4 libswscale7 libsz2 libtbb12
  libtbbbind-2-5 libtbbmalloc2 libtesseract5 libudfread0 libunibreak5 liburiparser1 libva-drm2 libva-x11-2 libva2 libvdpau1 libvidstab1.1 libvpl2 libx264-164 libx265-199 libxerces-c3.2t64 libxnvctrl0 libxvidcore4 libzimg2
  libzix-0-0 libzmq5 libzvbi-common libzvbi0t64 mesa-va-drivers mesa-vdpau-drivers mysql-common ocl-icd-libopencl1 pocketsphinx-en-us proj-bin proj-data python3-mlt unixodbc-common va-driver-all vdpau-driver-all
```
非常に多くの依存ライブラリがインストールされます。

- `libmlt7`: MLTライブラリの主要な部分
- `libmlt++7`: MLTライブラリのC++バインディング
- `libmlt-data`: MLTライブラリに関連するデータ
- その他、多数の依存パッケージ（例：`libavcodec60`、`libavformat60`、`libavutil58`など）、FFmpegなどに必要なライブラリ

インストールが完了したら、以下のPythonスクリプトを実行して、MLTが正しくインストールされているか確認します。

```bash
$ python3
Python 3.12.3 (main, Apr 10 2024, 05:33:47) [GCC 13.2.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import mlt

```
しかし残念ながらこの時点でエラーが発生してしまいました。

以下は問題解決のために試行した手順です。（ここは読み飛ばしてもらって構いません）
```bash
boxes@boxes:~$ dpkg -l ~ grep mlt
dpkg-query: /home/terms-boxes に一致するパッケージが見つかりません
dpkg-query: mlt に一致するパッケージが見つかりません
要望=(U)不明/(I)インストール/(R)削除/(P)完全削除/(H)保持
| 状態=(N)無/(I)インストール済/(C)設定/(U)展開/(F)設定失敗/(H)半インストール/(W)トリガ待ち/(T)トリガ保留
|/ エラー?=(空欄)無/(R)要再インストール (状態,エラーの大文字=異常)
||/ 名前           バージョン   アーキテクチ 説明
+++-==============-============-============-=================================
ii  grep           3.11-4build1 amd64        GNU grep, egrep and fgrep
boxes@boxes:~$ dpkg -l | grep mlt
ii  libmlt++7:amd64                               7.22.0-1build6                           amd64        MLT multimedia framework C++ wrapper (runtime)
ii  libmlt-data                                   7.22.0-1build6                           all          multimedia framework (data)
ii  libmlt7:amd64                                 7.22.0-1build6                           amd64        multimedia framework (runtime)
ii  python3-mlt                                   7.22.0-1build6                           amd64        multimedia framework (Python bindings)
boxes@boxes:~$ echo $PYTHONPATH

boxes@boxes:~$ python3 --version
Python 3.12.3
boxes@boxes:~$ export PYTHONPATH=$PYTHONPATH:/usr/lib/python3/dist-packages
boxes@boxes:~$ echo $PYTHONPATH
:/usr/lib/python3/dist-packages
boxes@boxes:~$ python3
Python 3.12.3 (main, Apr 10 2024, 05:33:47) [GCC 13.2.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import mlt
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ModuleNotFoundError: No module named 'mlt'
>>> 
```
この出力をみる限り、`Python3.12`と`MLT`のバインディングができていないのではないかと勘ぐりました。
そこで、`pyenv`を導入し、`Python3.10`の環境を作成します。
こちらも本題とは関係ないので読み飛ばしてください。

```bash
terms-boxes@boxes-standard-pc-i440fx-piix-1996:~$ sudo apt install -y curl make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev git



```




































#### 例: PythonでMLTを使用して動画にエフェクトを追加

まず、`lxml`ライブラリを使用してMLT XMLを生成し、それを使って動画にエフェクトを適用します。

```python
from lxml import etree

def create_mlt_xml_with_effect(input_video, output_xml):
    # MLT XMLのルート要素を作成
    mlt = etree.Element('mlt', version="6.26.1")

    # プロファイルを追加
    profile = etree.SubElement(mlt, 'profile', {
        'description': 'HD 1080p 25 fps',
        'width': '1920',
        'height': '1080',
        'progressive': '1',
        'frame_rate_num': '25',
        'frame_rate_den': '1',
        'colorspace': '709'
    })

    # プロデューサーを追加
    producer = etree.SubElement(mlt, 'producer', id="producer0")
    property_element = etree.SubElement(producer, 'property', name="resource")
    property_element.text = input_video
    property_element = etree.SubElement(producer, 'property', name="mlt_service")
    property_element.text = 'avformat'

    # プレイリストを追加
    playlist = etree.SubElement(mlt, 'playlist', id="playlist0")
    entry = etree.SubElement(playlist, 'entry', producer="producer0")

    # フェードインエフェクトを追加
    filter_element = etree.SubElement(mlt, 'filter', id="filter0", {
        'mlt_service': 'frei0r.alphaatop',
        'in': '0',
        'out': '50'
    })
    param = etree.SubElement(filter_element, 'property', name="0")
    param.text = '0.0=0;1.0=1'

    # タイムラインを追加
    tractor = etree.SubElement(mlt, 'tractor', id="tractor0")
    track = etree.SubElement(tractor, 'track', producer="playlist0")
    transition = etree.SubElement(tractor, 'transition', {
        'mlt_service': 'mix',
        'in': '0',
        'out': '250'
    })

    # XMLツリーをファイルに保存
    tree = etree.ElementTree(mlt)
    tree.write(output_xml, pretty_print=True, xml_declaration=True, encoding='UTF-8')

# 使用例
create_mlt_xml_with_effect("input_video.mp4", "output_with_effect.mlt")
```

---

## 補足
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



## 参考文献
- [MLT Multimedia Framework](https://www.mltframework.org/)
  ![](assets/2024-06-16-14-01-25.png)
- [MLT Framework(GitHub)](https://github.com/mltframework)
  ![](assets/2024-06-16-14-15-32.png)
