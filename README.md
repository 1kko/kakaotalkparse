# kakaotalkparse
Parse and Statistics from txt file exported from KakaoTalk.

# Screenshot
![github-large](https://github.com/1kko/kakaotalkparse/raw/main/example/screenshot.png)
# Install
```
pip install kakaotalkparse
```

# Usage
```
from kakaotalkparse import KakaoTalkParse

if __name__ == '__main__':
    ktparse = KakaoTalkParse()
    filename = "KakaoTalk_20210108_0846_18_555_group.txt"

    ktparse.open(filename)

    ktparse.setSrcTZ("Asia/Saigon")
    ktparse.setReportTz("Asia/Seoul")
    ktparse.setReportRange(startTime='2020-01-01', endTime='2020-12-31')

    data = ktparse.parse()
    stats = ktparse.stats(data)

    # print(stats)
    # for speaker in stats.keys():
    #     print(f"{speaker}: {stats[speaker]}")

    json = ktparse.conv2chartJS(stats)
    print(json)
```

# Results
```

어피치: {'totalCount': 3686, 'characters': 62119, 'urls': 141, 'photos': 172, 'files': 5, 'video': 5, 'emoticon': 108, 'activeTime': {'00': 12, '01': 5, '02': 1, '03': 0, '04': 5, '05': 14, '06': 153, '07': 269, '08': 247, '09': 284, '10': 247, '11': 174, '12': 397, '13': 331, '14': 328, '15': 296, '16': 219, '17': 162, '18': 136, '19': 102, '20': 65, '21': 94, '22': 112, '23': 33}, 'activeWeek': {'0': 668, '1': 756, '2': 697, '3': 679, '4': 529, '5': 243, '6': 114}, 'activeMonth': {'01': 197, '02': 331, '03': 448, '04': 246, '05': 387, '06': 245, '07': 130, '08': 189, '09': 314, '10': 496, '11': 290, '12': 413}}
쥬디: {'totalCount': 1981, 'characters': 32649, 'urls': 5, 'photos': 18, 'files': 0, 'video': 0, 'emoticon': 18, 'activeTime': {'00': 6, '01': 0, '02': 0, '03': 0, '04': 0, '05': 0, '06': 270, '07': 172, '08': 127, '09': 191, '10': 122, '11': 81, '12': 193, '13': 203, '14': 128, '15': 204, '16': 78, '17': 17, '18': 7, '19': 18, '20': 36, '21': 32, '22': 57, '23': 39}, 'activeWeek': {'0': 353, '1': 320, '2': 358, '3': 488, '4': 360, '5': 65, '6': 37}, 'activeMonth': {'01': 69, '02': 124, '03': 300, '04': 53, '05': 460, '06': 80, '07': 121, '08': 163, '09': 111, '10': 162, '11': 208, '12': 130}}
```
