"""실시간 계측DB 서비스 (GRE 데이터 통계)"""


class PortalMeasurementService:

    async def get_summary(self):
        """전체 KPI 요약"""
        return {
            "total_tags": 71612,
            "data_count_15min": 284530,
            "data_count_1hour": "2.3억",
            "region_count": 7,
            "site_count": 463,
            "avg_collect_rate": 86.6,
            "date_range": "2026-02-17 08:59 ~ 02-24 08:59"
        }

    async def get_regions(self):
        """유역별 현황"""
        return {
            "regions": [
                {"region": "충청지역지사", "offices": 12, "sites": 85, "tags": 16206, "ratio": 22.6, "collectRate": 92, "dataCount": "5,030만", "color": "#1677ff"},
                {"region": "한강권역본부", "offices": 11, "sites": 68, "tags": 15546, "ratio": 21.7, "collectRate": 89, "dataCount": "4,820만", "color": "#69b1ff"},
                {"region": "경남부산지역지사", "offices": 11, "sites": 100, "tags": 12320, "ratio": 17.2, "collectRate": 85, "dataCount": "3,820만", "color": "#fa8c16"},
                {"region": "낙동강권역본부", "offices": 8, "sites": 63, "tags": 9108, "ratio": 12.7, "collectRate": 88, "dataCount": "2,830만", "color": "#52c41a"},
                {"region": "금영섬권역본부", "offices": 7, "sites": 52, "tags": 7128, "ratio": 10.0, "collectRate": 78, "dataCount": "2,210만", "color": "#722ed1"},
                {"region": "광주전남지역지사", "offices": 10, "sites": 71, "tags": 6847, "ratio": 9.6, "collectRate": 83, "dataCount": "2,120만", "color": "#ff4d4f"},
                {"region": "강원지역지사", "offices": 2, "sites": 24, "tags": 4457, "ratio": 6.2, "collectRate": 91, "dataCount": "1,380만", "color": "#13c2c2"},
            ],
            "trend_data": {
                "labels": ["17일 12:00", "18일 00:00", "19일 00:00", "20일 12:00", "21일 00:00", "22일 00:00", "23일 12:00", "24일"],
                "values_15min": [14200, 15800, 12500, 18200, 14800, 16500, 13900, 15200, 18500, 14300, 15000, 18100, 14500, 15400],
                "values_1hour_avg": [13500, 14200, 13800, 15100, 14500, 14800, 14200, 15000]
            },
            "gauge_data": [
                {"region": "충청", "rate": 92, "color": "#52c41a"},
                {"region": "한강", "rate": 89, "color": "#52c41a"},
                {"region": "경남부산", "rate": 85, "color": "#fa8c16"},
                {"region": "낙동강", "rate": 88, "color": "#52c41a"},
                {"region": "금영섬", "rate": 78, "color": "#ff4d4f"},
                {"region": "광주전남", "rate": 83, "color": "#fa8c16"},
            ]
        }

    async def get_offices(self, region: str = None):
        """사무소별 사업장 현황"""
        return {
            "office_name": "과천관리단",
            "region_name": "수도권",
            "kpi": {
                "site_count": 7,
                "tag_total": 3857,
                "collecting": 3057,
                "uncollecting": 800,
                "data_count": "1.7억",
                "date_range": "2025-10-01 ~ 2026-02-09",
                "days": 132
            },
            "sites": [
                {"name": "G81", "tags": 2149, "collectRate": 38.6, "collectTags": 830, "uncollect": 1319, "dataCount": "8,400만", "status": "경고"},
                {"name": "시흥정수장", "tags": 379, "collectRate": 97.8, "collectTags": 371, "uncollect": 8, "dataCount": "1,480만", "status": "정상"},
                {"name": "반월정수장", "tags": 201, "collectRate": 97.5, "collectTags": 196, "uncollect": 5, "dataCount": "780만", "status": "정상"},
                {"name": "거점가압장", "tags": 132, "collectRate": 83.4, "collectTags": 110, "uncollect": 22, "dataCount": "520만", "status": "정상"},
                {"name": "안산가압장", "tags": 104, "collectRate": 100, "collectTags": 104, "uncollect": 0, "dataCount": "410만", "status": "정상"},
                {"name": "구천암", "tags": 68, "collectRate": 100, "collectTags": 68, "uncollect": 0, "dataCount": "270만", "status": "정상"},
                {"name": "경인가압장", "tags": 94, "collectRate": 90.3, "collectTags": 85, "uncollect": 9, "dataCount": "370만", "status": "정상"},
            ],
            "trend_data": {
                "labels": ["10월", "11월", "12월", "1월", "2월"],
                "values": [180, 190, 175, 200, 165, 185, 195, 172, 188, 205, 178, 192, 168]
            }
        }

    async def get_site_detail(self, site: str = None):
        """사업장 태그 상세"""
        return {
            "site_name": "G81",
            "office_name": "과천관리단",
            "region_name": "수도권",
            "kpi": {
                "tag_count": 2149, "collecting": 1293, "uncollecting": 856,
                "data_count": "1.6억", "date_range": "2025-10-01 ~ 02-09", "days": 132,
                "valid_rate": 39.85, "collect_rate": 60.15,
                "recent_normal": 1800, "recent_warn": 0, "recent_error": 349
            },
            "donuts": {
                "quantity": [{"label": "수도권", "value": 1521, "color": "#fa8c16"}, {"label": "충청권", "value": 412, "color": "#722ed1"}, {"label": "기타", "value": 216, "color": "#13c2c2"}],
                "status": [{"label": "정상", "value": 1982, "color": "#1677ff"}, {"label": "미수집", "value": 167, "color": "#f0f0f0"}],
                "phase": [{"label": "수집전", "value": 1778, "color": "#52c41a"}, {"label": "수집후", "value": 371, "color": "#d9d9d9"}]
            },
            "daily_bars": [88, 84, 80, 76, 72, 68, 64, 60, 56, 52, 48, 44, 40, 36],
            "top_tags": [41, 35, 30, 25, 22, 20, 17, 15]
        }

    async def get_tags(self, site: str = None):
        """태그 목록"""
        return [
            {"tagName": "TAG001", "status": "100%", "desc": "유량계_전류센서(합천)(10장) 수처리-1", "category": "GSCL0035-10-41270", "supplier": "계측", "tagType": "전류(A)", "dataCount": "1시간", "section": 90, "unit": "A", "id": "053"},
            {"tagName": "TAG002", "status": "100%", "desc": "유량계_전류센서(합천)(101) 수처리-2", "category": "GSCL0035-10-41270", "supplier": "계측", "tagType": "전류(A)", "dataCount": "1시간", "section": 90, "unit": "A", "id": "064"},
            {"tagName": "TAG003", "status": "100%", "desc": "유량계_전류센서(합천)(10) 수처리-3", "category": "GSCL0035-10-41270", "supplier": "계측", "tagType": "전류(A)", "dataCount": "1시간", "section": 90, "unit": "A", "id": "005"},
            {"tagName": "TAG004", "status": "100%", "desc": "전력계_MCC-시설+태양광(구/시) 8호", "category": "SHNO355-10-41270", "supplier": "전력", "tagType": "전력(kW)", "dataCount": "1시간", "section": 90, "unit": "kW", "id": "201"},
            {"tagName": "TAG005", "status": "85%", "desc": "전력계_MCC-4호 전력부(2진입) 8호", "category": "SHNO355-10-41270", "supplier": "전력", "tagType": "전력(kW)", "dataCount": "1시간", "section": 90, "unit": "kW", "id": "202"},
            {"tagName": "TAG006", "status": "100%", "desc": "전력계_MCC-4로+태양(6진입) 8호", "category": "SHNO355-10-41270", "supplier": "전력", "tagType": "전력(kW)", "dataCount": "1시간", "section": 90, "unit": "kW", "id": "203"},
            {"tagName": "TAG007", "status": "100%", "desc": "압력계_송수관 압력센서 FLT", "category": "BYAV1333-35-41270", "supplier": "압력", "tagType": "압력(MPa)", "dataCount": "1시간", "section": 90, "unit": "MPa", "id": "204"},
            {"tagName": "TAG008", "status": "100%", "desc": "압력계_배수지 압력센서 FLT", "category": "BYAV1333-35-41270", "supplier": "압력", "tagType": "전류(A)", "dataCount": "1시간", "section": 90, "unit": "A", "id": "205"},
            {"tagName": "TAG009", "status": "100%", "desc": "수위계_취수장 수위센서 L-01", "category": "WLVL2010-20-31240", "supplier": "수위", "tagType": "수위(m)", "dataCount": "15분", "section": 85, "unit": "m", "id": "301"},
            {"tagName": "TAG010", "status": "100%", "desc": "수위계_정수지 수위센서 L-02", "category": "WLVL2010-20-31240", "supplier": "수위", "tagType": "수위(m)", "dataCount": "15분", "section": 85, "unit": "m", "id": "302"},
            {"tagName": "TAG011", "status": "85%", "desc": "유량계_원수 유입 유량센서 F-01", "category": "FLOW3015-30-21150", "supplier": "유량", "tagType": "유량(m3/h)", "dataCount": "1시간", "section": 92, "unit": "m3/h", "id": "401"},
            {"tagName": "TAG012", "status": "100%", "desc": "유량계_송수 유량센서 F-02", "category": "FLOW3015-30-21150", "supplier": "유량", "tagType": "유량(m3/h)", "dataCount": "1시간", "section": 92, "unit": "m3/h", "id": "402"},
            {"tagName": "TAG013", "status": "100%", "desc": "수질계_탁도 측정센서 TU-01", "category": "QUAL4020-40-11080", "supplier": "수질", "tagType": "탁도(NTU)", "dataCount": "15분", "section": 88, "unit": "NTU", "id": "501"},
            {"tagName": "TAG014", "status": "100%", "desc": "수질계_잔류염소 측정 CL-01", "category": "QUAL4020-40-11080", "supplier": "수질", "tagType": "염소(mg/L)", "dataCount": "15분", "section": 88, "unit": "mg/L", "id": "502"},
            {"tagName": "TAG015", "status": "100%", "desc": "수질계_pH 측정센서 PH-01", "category": "QUAL4020-40-11080", "supplier": "수질", "tagType": "pH", "dataCount": "15분", "section": 88, "unit": "pH", "id": "503"},
            {"tagName": "TAG016", "status": "85%", "desc": "온도계_원수 수온센서 TE-01", "category": "TEMP5010-50-41270", "supplier": "온도", "tagType": "온도(C)", "dataCount": "1시간", "section": 90, "unit": "C", "id": "601"},
        ]


portal_measurement_service = PortalMeasurementService()
