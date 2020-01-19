import React, { Component } from 'react'
import {
    Container,
    Row,
    Col,
    Card,
    CardBody,
    Button,
    Input
} from 'reactstrap';
import Dropzone from 'react-dropzone';
import './SearchPage.css';
import axios from 'axios';

import { API_BASE } from '../App';

export default class SearchPage extends Component {
    constructor() {
        super();
        this.onDrop = (files) => {
            this.setState({file: files[0]})
        };
        
        this.state = {
            file: null,
            searchTerm: ''
        };

        this.sendSearchRequest = this.sendSearchRequest.bind(this);
    }

    async sendSearchRequest() {
        if (this.state.file == null) return;
        const toBase64 = file => new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = () => resolve(reader.result);
            reader.onerror = error => reject(error);
        });

        const data = {
            'input': await toBase64(this.state.file.path),
            'query': this.state.searchTerm
        };

        axios({
            url: `${API_BASE}/api/search`,
            data: data,
            headers: {
                'Content-Type': 'application/json'
            }
        }).then((response) => {
            console.log(response.data);
        }).catch((error) => {
            console.log(error);
        });
    }

    searchTermsChanged(e) {
        this.setState({searchTerm: e.target.value})
    }

    render() {
        let dropzoneLabel = 'Drag \'n\' drop a file, or click to get started';
        if (this.state.file != null) {
            dropzoneLabel = this.state.file.name;
        }

        return (
            <Container>
                <Row>
                    <Col sm="9" md="9" lg="7" className="mx-auto">
                        <h1 className="text-center display-1 my-5 title-text">Syft</h1>
                        <Card className="my-5">
                            <CardBody>
                                <Dropzone onDrop={this.onDrop} accept="audio/*,video/*" maxSize="104857600">
                                    {({getRootProps, getInputProps, isDragActive}) => (
                                    <div {...getRootProps({className: 'dropzone my-4' + (isDragActive ? ' dropzone-active' : '')})}>
                                        <input {...getInputProps()} />
                                        <p className="text-center">{dropzoneLabel}</p>
                                    </div>
                                )}
                                </Dropzone>
                                <Input type="text" id="inputSearchTerms" placeholder="Keywords" 
                                    value={this.state.searchTerm} onChange={this.searchTermsChanged} />

                                <hr className="my-4" />
                                <Button size="lg" color="dark" rounded outline block onClick={this.sendSearchRequest}>Search</Button>
                            </CardBody>
                        </Card>
                    </Col>
                </Row>
            </Container>
        )
    }
}
