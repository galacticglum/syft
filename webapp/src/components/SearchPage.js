import React, { Component } from 'react'
import {
    Container,
    Row,
    Col,
    Card,
    CardBody,
    Button,
    Input,
    Spinner,
    CustomInput,
    Alert
} from 'reactstrap';
import Dropzone from 'react-dropzone';
import './SearchPage.css';
import axios from 'axios';

import { API_BASE } from '../App';
import ResultsPage from './ResultsPage';

export default class SearchPage extends Component {
    constructor() {
        super();
        this.onDrop = (files) => {
            this.setState({file: files[0]})
        };
        
        this.state = {
            file: null,
            searchTerm: '',
            isLoading: false,
            queryResult: null,
            isContextSearch: false,
            hasError: false
        };

        this.sendSearchRequest = this.sendSearchRequest.bind(this);
        this.searchTermsChanged = this.searchTermsChanged.bind(this);
        this.contextSearchToggleChanged =  this.contextSearchToggleChanged.bind(this);
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
            'file_input': await toBase64(this.state.file),
            'query': this.state.searchTerm,
            'is_context_search': this.state.isContextSearch
        };

        this.setState({isLoading: true, hasError: false});
        axios.post(`${API_BASE}/api/search/`, {
            ...data,
            headers: {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json',
            }
        }).then((response) => {
            console.log(response.data);
            this.setState({isLoading: false, queryResult: response.data});
        }).catch((error) => {
            this.setState({isLoading: false, hasError: true});
            console.log(error);
        });
    }

    searchTermsChanged(e) {
        this.setState({searchTerm: e.target.value})
    }

    contextSearchToggleChanged(e) {
        this.setState({isContextSearch: e.target.checked});
    }

    render() {
        let dropzoneLabel = 'Drag \'n\' drop a file, or click to get started';
        if (this.state.file != null) {
            dropzoneLabel = this.state.file.name;
        }

        if (this.state.queryResult == null) {
            return (
                <Container>
                    <Row>
                        <Col sm="9" md="9" lg="7" className="mx-auto">
                            <h1 className="text-center display-1 my-5 title-text" onClick={() => window.location.reload()}>Syft</h1>
                            {
                                (this.state.hasError ?
                                    (<Alert color="danger" className="mt-5">
                                        Uh-oh! We couldn't process your request. This is probably an issue with our servers. Please try again later.
                                    </Alert>)
                                : null)
                            }
                            
                            <Card>
                                <CardBody>
                                    <Dropzone onDrop={this.onDrop} accept="audio/*,video/*" maxSize={104857600} disabled={this.state.isLoading}>
                                        {({getRootProps, getInputProps, isDragActive}) => (
                                        <div {...getRootProps({className: 'dropzone mb-4' + (isDragActive ? ' dropzone-active' : '')})}>
                                            <input {...getInputProps()} />
                                            <p className="text-center">{dropzoneLabel}</p>
                                        </div>
                                    )}
                                    </Dropzone>
                                    <Input type="text" id="inputSearchTerms" placeholder="Search" disabled={this.state.isLoading}
                                        value={this.state.searchTerm} onChange={this.searchTermsChanged} />
                                    <CustomInput className="pt-3" type="switch" id="contextSearchToggle" label="Context-based search"
                                        onChange={this.contextSearchToggleChanged} value={this.state.isContextSearch} />

                                    <hr className="my-4" />
                                    <Button disabled={this.state.isLoading} size="lg" color="dark" outline block 
                                        onClick={this.sendSearchRequest}>
                                        {this.state.isLoading ? (<Spinner />) : 'Search'}
                                    </Button>
                                </CardBody>
                            </Card>
                        </Col>
                    </Row>
                </Container>
            )
        }
        else {
            return (
                <ResultsPage accessLink={this.state.queryResult['access_link']} elapsedTime={this.state.queryResult['elapsed_time']} 
                    matchResults={this.state.queryResult['matches']} queryText={this.state.searchTerm} />
            );
        }
    }
}
