# syft
An text-based audio search engine developed in Python for UofTHacks VII. Submission available on [Devpost](https://devpost.com/software/syft-dk4i8a).

<img src="https://challengepost-s3-challengepost.netdna-ssl.com/photos/production/software_photos/000/913/746/datas/original.png" width="800" style="text-align: center" />

<hr>

## Inspiration
Searching large quantities of information can be a very grueling, repetitive, and boring task. While there are tools that aim to streamline this process for text-based data (such as Ctrl+F), there is no good similar solution for audio and video based data. Our goal is to help minimize this problem by speeding up the time that it takes to search in audio files.

## What it does
Syft is a web-based tool for searching phrases within audio recordings. It can extract both the exact timestamps where the phrase was uttered, along with the sentence containing it. 

## How we built it
Syft is powered by Google Cloud Speech to Text recognition. The audio recordings are transcribed and then searched. Finally, the matches are cross-referenced with the transcription to determine the timestamps.

## Challenges we ran into
* Resolving search query matches regardless of punctuation, contractions, and other natural language features.
* Optimizing the backend, most notably the audio transcription pipeline, to speedily serve search results.
* Deploying the backend API server to Google App Engine. 

## Accomplishments that we're proud of
* A clean and elegant frontend UI
* Relatively fast search queries

## What we learned
* Google Cloud App Engine creation and deployment; flexible environments with custom runtimes using Dockerfile.

## What's next for Syft
* Providing an option to download search results as audio/video clips (either individually or as a supercut).
* Developing a custom speech-to-text model, removing the network latency that comes with Google's API, and thus most likely speeding up the application.
* Expanding the search engine to graphics as well (i.e. searching for text within frames of a video).
