from datetime import datetime, timedelta
from dateutil import parser as dateParser  # pip install python-datetuil
import re
import json
import pytz


class KakaoTalkParse():
    """
    Parses KakaoTalk Chat TXT Logs
    """

    def __init__(self):
        # set timezone
        self.srcTZ = pytz.timezone("Asia/Saigon")
        self.reportTz = pytz.timezone("Asia/Seoul")

        # 2020-01-01 00:00:00부터 현재까지
        self.reportStart = self.reportTz.localize(
            datetime(2020, 1, 1, 0, 0, 0))
        self.reportEnd = self.reportTz.localize(
            datetime.now())

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

    def setReportRange(self, startTime, endTime):
        """
        Set date range
        """
        self.reportStart = self.reportTz.localize(dateParser.parse(startTime))
        self.reportEnd = self.reportTz.localize(dateParser.parse(endTime))

    def setSrcTZ(self, timezone="Asia/Seoul"):
        self.srcTZ = pytz.timezone(timezone)

    def setReportTz(self, timezone="Asia/Seoul"):
        self.reportTz = pytz.timezone(timezone)

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
                retval[speaker] = {
                    'totalCount': 0, 'characters': 0, 'urls': 0, 'photos': 0, 'files': 0, 'videos': 0, 'emoticons': 0,
                    'activeHour': {
                        "00": 0,  "01": 0,  "02": 0,  "03": 0,  "04": 0,  "05": 0,
                        "06": 0,  "07": 0,  "08": 0,  "09": 0,  "10": 0,  "11": 0,
                        "12": 0,  "13": 0,  "14": 0,  "15": 0,  "16": 0,  "17": 0,
                        "18": 0,  "19": 0,  "20": 0,  "21": 0,  "22": 0,  "23": 0,
                    },
                    'activeWeek': {
                        "Mon": 0,
                        "Tue": 0,
                        "Wed": 0,
                        "Thu": 0,
                        "Fri": 0,
                        "Sat": 0,
                        "Sun": 0,
                    },
                    'activeMonth': {
                        "Jan": 0,  "Feb": 0,  "Mar": 0,  "Apr": 0,  "May": 0, "Jun": 0,
                        "Jul": 0,  "Aug": 0,  "Sep": 0,  "Oct": 0,  "Nov": 0, "Dec": 0,
                    },
                    'activeDays': {
                    }
                }

                activeDaysList = [self.reportStart + timedelta(days=x) for x in range(
                    0, (self.reportEnd-self.reportStart).days)]
                activeDaysKeys = [x.strftime("%Y-%m-%d")
                                  for x in activeDaysList]
                for activeDay in activeDaysKeys:
                    retval[speaker]['activeDays'][activeDay] = 0

            # report range condition
            if item['msgTime'] >= self.reportStart and item['msgTime'] <= self.reportEnd:
                retval[speaker]['totalCount'] += 1
                retval[speaker]['characters'] += len(item['message'])

                if item['message'].find("http://") >= 0 or item['message'].find("https://") >= 0:
                    retval[speaker]['urls'] += 1

                if item['message'] == "사진":
                    retval[speaker]['photos'] += 1

                if item['message'] == "동영상":
                    retval[speaker]['videos'] += 1

                if item['message'] == "이모티콘":
                    retval[speaker]['emoticons'] += 1

                if item['message'].startswith("파일: "):
                    retval[speaker]['files'] += 1

                hourKey = item['msgTime'].strftime("%H")
                retval[speaker]['activeHour'][hourKey] += 1

                weekKey = item['msgTime'].strftime("%a")
                retval[speaker]['activeWeek'][weekKey] += 1

                monthKey = item['msgTime'].strftime("%b")
                retval[speaker]['activeMonth'][monthKey] += 1

                dayKey = item['msgTime'].strftime("%Y-%m-%d")
                if dayKey not in retval[speaker]['activeDays'].keys():
                    retval[speaker]['activeDays'][dayKey] = 0
                retval[speaker]['activeDays'][dayKey] += 1

        return retval

    def conv2chartJS(self, stats):
        retval = {
            'reportInfo': {
                'reportStart': self.reportStart.strftime("%Y-%m-%d"),
                'reportEnd': self.reportEnd.strftime("%Y-%m-%d"),
                'reportTZ': self.reportTz.zone
            },
        }
        borderColors = [
            ("blue", "rgb(54, 162, 235)"),
            ("green", "rgb(75, 192, 192)"),
            ("grey", "rgb(201, 203, 207)"),
            ("orange", "rgb(255, 159, 64)"),
            ("purple", "rgb(153, 102, 255)"),
            ("red", "rgb(255, 99, 132)"),
            ("yellow", "rgb(255, 205, 86)"),
        ]
        backgroundColors = [
            ("blue", "rgba(54, 162, 235, 0.5)"),
            ("green", "rgba(75, 192, 192, 0.5)"),
            ("grey", "rgba(201, 203, 207, 0.5)"),
            ("orange", "rgba(255, 159, 64, 0.5)"),
            ("purple", "rgba(153, 102, 255, 0.5)"),
            ("red", "rgba(255, 99, 132, 0.5)"),
            ("yellow", "rgba(255, 205, 86, 0.5)")
        ]

        # totalCount, characters, urls, photos, files, videos, emoticons
        for category in ['totalCount', 'characters', 'urls', 'photos', 'files', 'videos', 'emoticons']:
            retval[category] = {
                'labels': [],
                'datasets': []
            }
            p = {
                'label': 'Dataset 1',
                'data': [],
                'backgroundColor': [],
                'borderColor': [],
                'borderWidth': 1,
            }

            counter = 0
            for speaker in stats.keys():
                colorIndex = counter % len(backgroundColors)
                counter += 1
                retval[category]['labels'].append(speaker)
                p['data'].append(stats[speaker][category])
                p['backgroundColor'].append(backgroundColors[colorIndex][1])
                p['borderColor'].append(borderColors[colorIndex][1])

            retval[category]['datasets'].append(p)

        # activeTime, activeWeek, activeMonth, activeDays
        for category in ['activeHour', 'activeWeek', 'activeMonth', 'activeDays']:
            retval[category] = {
                'labels': list(stats[list(stats.keys())[0]][category].keys()),
                'datasets': []
            }

            counter = 0
            for speaker in stats.keys():
                colorIndex = counter % len(backgroundColors)
                counter += 1
                p = {
                    'label': speaker,
                    'data': list(stats[speaker][category].values()),
                    'backgroundColor': backgroundColors[colorIndex][1],
                    'borderColor': borderColors[colorIndex][1],
                    'borderWidth': 1,
                }
                retval[category]['datasets'].append(p)

        with open('stats.json', 'w', encoding='utf-8') as fp:
            json.dump(retval, fp, ensure_ascii=False, indent=4)
        return json.dumps(retval)


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
