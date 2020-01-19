import React, { Component } from 'react'
import {
    Container,
    Row,
    Col,
    Card,
    CardBody,
    Button,
    ListGroup,
    ListGroupItem,
    ListGroupItemHeading,
    ListGroupItemText
} from 'reactstrap';
import { API_BASE } from '../App';
import './ResultsPage.css';

export default class ResultsPage extends Component {
    render() {
        return (
            <Container>
                <Row>
                    <Col lg="10" xl="10" className="mx-auto">
                        <h1 className="text-center display-1 my-5 title-text">Syft</h1>
                        <Card className="results-card flex-row my-5">
                            <div className="card-img-left d-none d-md-flex">
                                <div class="list-group w-100">
                                    <a href="#" class="list-group-item list-group-item-action flex-column align-items-start">
                                        <p class="mb-1">Matched "ou pe" (3.9 - 5.6 seconds).</p>
                                        <small class="text-muted">96% confident.</small>
                                    </a>
                                    <a href="#" class="list-group-item list-group-item-action flex-column align-items-start">
                                        <p class="mb-1">Matched "ou pe" (3.9 - 5.6 seconds).</p>
                                        <small class="text-muted">96% confident.</small>
                                    </a>
                                    <a href="#" class="list-group-item list-group-item-action flex-column align-items-start">
                                        <p class="mb-1">Matched "ou pe" (3.9 - 5.6 seconds).</p>
                                        <small class="text-muted">96% confident.</small>
                                    </a>
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
