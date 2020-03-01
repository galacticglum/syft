import React, { Component } from 'react'
import {
    Container,
    Row,
    Col,
    Card,
    CardBody
} from 'reactstrap';
import { API_BASE } from '../App';
import './ResultsPage.css';

import AudioPlayer from 'react-h5-audio-player';
import 'react-h5-audio-player/lib/styles.css';

export default class ResultsPage extends Component {
    constructor() {
        super();
        this.onMatchResultClicked = this.onMatchResultClicked.bind(this);
    }

    onMatchResultClicked(event, matchResult) {
        this.player.audio.currentTime = matchResult.start_time;
        this.player.audio.play();
        console.log(this.player);
    }

    render() {
        const matchResultItems = this.props.matchResults.map((matchResult, index) => {
            let extraClassName = '';
            if (index == this.props.matchResults.length - 1) {
                extraClassName = 'list-group-item-last'
            }

            return (
                <a key={index} href="#" onClick={(event) => this.onMatchResultClicked(event, matchResult)}
                    className={"h-100 list-group-item list-group-item-action flex-column align-items-start " + extraClassName}>
                    {/* <p className="mb-1">{matchResult.start_time} - {matchResult.end_time} seconds</p>
                    <p className="font-weight-bold">"{matchResult.transcript}"</p>
                    <small className="text-muted">{(matchResult.confidence * 100).toFixed(2)}% confident</small> */}
                    <h5 class="mb-1 card-title font-weight-bold">"{matchResult.transcript}"</h5>
                    <h6 class="card-subtitle mb-2">{matchResult.start_time} - {matchResult.end_time} seconds</h6>
                    <small class="text-muted card-text font-small">{(matchResult.confidence * 100).toFixed(2)}% confident</small>
                </a>
            );
        });
        
        if (this.props.matchResults.length > 0) {
            return (
                <Container>
                    <Row>
                        <Col lg="10" xl="10" className="mx-auto">
                            <h1 className="text-center display-1 my-5 title-text" onClick={() => window.location.reload()}>Syft</h1>
                            <p className="h3 text-muted font-italic">Search results for "{this.props.queryText}" ({this.props.matchResults.length}) in {this.props.elapsedTime.toFixed(3)} seconds</p>
                            <Card className="results-card flex-row mt-3 mb-5">
                                <div className="card-img-left d-none d-md-flex">
                                    <div className="list-group w-100">
                                        {matchResultItems}
                                    </div>
                                </div>
                                <CardBody>
                                    <AudioPlayer className="text-center" ref={c => (this.player=c)} src={this.props.accessLink} showDownloadProgress={false} />
                                </CardBody>
                            </Card>
                        </Col>
                    </Row>
                </Container>
            );
        } else {
            return (
                <Container>
                    <Row>
                        <Col lg="10" xl="10" className="mx-auto">
                            <h1 className="text-center display-1 my-5 title-text" onClick={() => window.location.reload()}>Syft</h1>
                            <Card className="results-card mt-3 mb-5">
                                <CardBody>
                                    <p className="h3 text-muted font-italic">Uh-oh! We couldn't find anything.</p>
                                </CardBody>
                            </Card>
                        </Col>
                    </Row>
                </Container>
            );
        }
    }
}
