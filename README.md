# Namuwiki Extractor
- [기존 NamuwikiExtractor](https://github.com/nawnoes/NamuwikiExtractor)를 클론하였습니다.
- 기존 레포에서 사용하는 kss<2의 경우 결과를 살펴봤을 때, 문장이 잘 분절이 안되는 경우들을 확인하였습니다.
- kss 3.x가 sentence segmentation 결과가 더 좋으나 형태소 분석기를 사용함에 따라 속도가 더 느린 문제가 있어서 kss 3.x에 맞게 수정 및 multiprocessing이 가능하게 refactoring을 진행하였습니다


## 사용법
#### 0. 나무위기 덤프 다운로드
[나무위키 덤프 다운로드 페이지](https://namu.wiki/w/%EB%82%98%EB%AC%B4%EC%9C%84%ED%82%A4:%EB%8D%B0%EC%9D%B4%ED%84%B0%EB%B2%A0%EC%9D%B4%EC%8A%A4%20%EB%8D%A4%ED%94%84)에서 나무위키 덤프 다운로드 


### 1. Mecab 설치
- [Mecab 홈페이지](https://bitbucket.org/eunjeon/mecab-ko) 참조
- 

### 2. 패키지 설치
```text
ujson
kss
namu-wiki-extractor
python-mecab-ko
```

- 해당 레포를 다운로드 후 pip install -r requirements.txt로 필요 라이브러리를 설치합니다.


#### 3. 명령어 실행
`NamuwikiExtractor.py` 경로에서 아래 명령어 실행. 40코어 기준 6시간 정도 소요
```sh
python3 NamuwikiExtractor.py --dump-path "[나무위키 덤프 경로]" --output-dir "[저장 폴더 경로]" --num-workers "[워커 개수]"
```
