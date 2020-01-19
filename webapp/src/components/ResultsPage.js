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

export default class ResultsPage extends Component {
    render() {
        const matchResultItems = this.props.matchResults.map((matchResult, index) => {
            let extraClassName = '';
            if (index == this.props.matchResults.length - 1) {
                extraClassName = 'list-group-item-last'
            }

            return (
                <a key={index} href="#" className={"list-group-item list-group-item-action flex-column align-items-start " + extraClassName}>
                    <p className="mb-1">{matchResult.start_time} - {matchResult.end_time} seconds</p>
                    <small className="text-muted">{matchResult.confidence}% confident</small>
                </a>
            );
        });

        return (
            <Container>
                <Row>
                    <Col lg="10" xl="10" className="mx-auto">
                        <h1 className="text-center display-1 my-5 title-text">Syft</h1>
                        <Card className="results-card flex-row my-5">
                            <div className="card-img-left d-none d-md-flex">
                                <div className="list-group w-100">
                                    {matchResultItems}
                                </div>
                            </div>
                            <CardBody>

                            </CardBody>
                        </Card>
                    </Col>
                </Row>
            </Container>
        );
    }
}
