"""
Parses KakaoTalk Chat TXT Logs
"""

from datetime import datetime
from dateutil import parser as dateParser  # pip install python-datetuil
import re
import pytz


class KakaoTalkParse():
    def __init__(self):
        # set timezone
        self.srcTZ = pytz.timezone("Asia/Saigon")
        self.reportTz = pytz.timezone("Asia/Seoul")

        # global variables
        self._prev_speaker = None
        self._prev_msgTime = None
        self.contents = None

    def _parse_day(self, line):
        """
        한글 형식 날짜를 읽어서 datetime 형식으로 변환한다.
        """
        datestring = line.replace("년 ", "-").replace("월 ",
                                                     "-").replace("일", " ").split(" ")[1]
        return datetime.strptime(datestring, "%Y-%m-%d").date()

    def _generateDateIndex(self, contents):
        """
        파일을 전체 스캔하여 날짜별로 시작행과 종료행을 리턴한다
        """

        # 파일을 전체 스캔하여 날짜 형식이 있는 행을 저장한다.
        index = list()
        cnt = 1  # lineno starts from 1
        for line in contents:
            if line.startswith("--------------- ") and line.endswith(" ---------------\r\n"):
                index.append({'date': self._parse_day(line), 'lineStart': cnt})
            cnt += 1

        # index를 다시 한번 돌면서 종료라인을 구한다.
        for i in range(0, len(index)):
            # to avoid IndexError
            if len(index)-1 == i:
                lineEnd = cnt-1
            else:
                lineEnd = index[i+1]['lineStart']
            index[i]['lineEnd'] = lineEnd-1

        return index

    def _parseLine(self, baseDate, line):
        """
        "[어피치] [오후 10:38] ㄷㄷㄷ" 을 regex를 이용하여 이름, 시간, 내용으로 변환하고,
        baseDate를 기준으로 날짜+시간을 생성한다.
        """
        item = re.search(r'^\[(.*)\]\ \[(.*[0-9:]+)\]\ (.*)\n', line)
        try:
            if item is not None:
                speaker = item.group(1)
                timeStr = item.group(2)
                if timeStr.startswith("오전"):
                    timeStr = timeStr.replace("오전 ", "")+" AM"
                elif timeStr.startswith("오후"):
                    timeStr = timeStr.replace("오후 ", "")+" PM"
                msgTime = dateParser.parse(baseDate.strftime(
                    "%Y-%m-%d ")+timeStr)
                msgTime = self.srcTZ.localize(msgTime)

                message = item.group(3).replace("\r", "").replace("\n", "")

                self._prev_speaker = speaker
                self._prev_msgTime = msgTime
                return {"speaker": speaker, "msgTime": msgTime, "message": message}
            else:
                message = line.replace("\r", "").replace("\n", "")
                return {"type": "append", "speaker": self._prev_speaker, "msgTime": self._prev_msgTime, "message": message}
        except:
            message = line.replace("\r", "").replace("\n", "")
            return {"type": "exception", "speaker": self._prev_speaker, "msgTime": self._prev_msgTime, "message": message}

    def _generateMessageIndex(self, indexItem, contents):
        cnt = indexItem['lineStart']
        retval = []
        for line in contents:
            cnt += 1
            d = self._parseLine(indexItem['date'], line)
            d['lineno'] = cnt
            retval.append(d)
        return retval

    def open(self, filename):
        """
        Reads kakaotalk export text file.

        filename: filepath and name.
        eg: KakaoTalk_20210108_0846_18_555_group.txt
        """
        with open(filename, 'rt', newline='', encoding='utf-8') as fp:
            self.contents = fp.readlines()
        return self.contents

    def parse(self, contents=None):
        """
        parse contents

        contents: all text data from file.
        """
        if contents == None:
            contents = self.contents
        indexItems = self._generateDateIndex(contents)
        data = list()

        for indexItem in indexItems:
            item = self._generateMessageIndex(
                indexItem, contents[indexItem['lineStart']:indexItem['lineEnd']])
            data = data + item

        return data

    def stats(self, chatData):
        retval = dict()
        """
        {
            'type': 'append',
            'speaker': '어피치', 
            'msgTime': datetime.datetime(2021, 1, 8, 7, 39), 
            'message': '사실적이고 관대하며 개방적이고 사람이나 사물에 대한 선입견이 별로 없다. 강한 현실 감각으로 타협책을 모색하고 문제를 해결하는 능력이 뛰어나다. 센스 있고 유머러스하다. 어디서든 적응을 잘 하고 친구와 어울리기를 좋아한다.', 
            'lineno': 24179
        }
        """

        for item in chatData:
            speaker = item['speaker']
            if speaker not in retval.keys():
                # initialize speaker
                retval[speaker] = {'totalCount': 0, 'characters': 0, 'urls': 0, 'photos': 0, 'files': 0, 'video': 0, 'emoticon': 0,
                                   'activeTime': {
                                       "00": 0,  "01": 0,  "02": 0,  "03": 0,  "04": 0,  "05": 0,
                                       "06": 0,  "07": 0,  "08": 0,  "09": 0,  "10": 0,  "11": 0,
                                       "12": 0,  "13": 0,  "14": 0,  "15": 0,  "16": 0,  "17": 0,
                                       "18": 0,  "19": 0,  "20": 0,  "21": 0,  "22": 0,  "23": 0,
                                   },
                                   'activeWeek': {
                                       "0": 0,  # monday
                                       "1": 0,  # tuesday
                                       "2": 0,  # wednesday
                                       "3": 0,  # thursday
                                       "4": 0,  # friday
                                       "5": 0,  # saturday
                                       "6": 0,  # sunday
                                   },
                                   'activeMonth': {
                                       "01": 0,  "02": 0,  "03": 0,  "04": 0,  "05": 0, "06": 0,
                                       "07": 0,  "08": 0,  "09": 0,  "10": 0,  "11": 0, "12": 0,
                                   }
                                   }
            # 2020-01-01 부터 2020-12-31까지
            startTime = self.reportTz.localize(datetime(2020, 1, 1, 0, 0, 0))
            endTime = self.reportTz.localize(
                datetime(2020, 12, 31, 23, 59, 59))

            if item['msgTime'] >= startTime and item['msgTime'] <= endTime:

                retval[speaker]['totalCount'] += 1
                retval[speaker]['characters'] += len(item['message'])

                if item['message'].find("http://") >= 0 or item['message'].find("https://") >= 0:
                    retval[speaker]['urls'] += 1

                if item['message'] == "사진":
                    retval[speaker]['photos'] += 1

                if item['message'] == "동영상":
                    retval[speaker]['video'] += 1

                if item['message'] == "이모티콘":
                    retval[speaker]['emoticon'] += 1

                if item['message'].startswith("파일: "):
                    retval[speaker]['files'] += 1

                hourKey = item['msgTime'].strftime("%H")
                retval[speaker]['activeTime'][hourKey] += 1

                weekKey = str(item['msgTime'].weekday())
                retval[speaker]['activeWeek'][weekKey] += 1

                monthKey = item['msgTime'].strftime("%m")
                retval[speaker]['activeMonth'][monthKey] += 1

        return retval


def main():
    ktparse = KakaoTalkParse()
    filename = "KakaoTalk_20210108_0846_18_555_group.txt"

    ktparse.open(filename)
    data = ktparse.parse()
    stats = ktparse.stats(data)

    for speaker in stats.keys():
        print(f"{speaker}: {stats[speaker]}")


if __name__ == '__main__':
    main()
