import React, { Component } from 'react'
import {
    Container,
    Row,
    Col,
    Card,
    CardBody,
    CardTitle,
    Button,
    Input,
    Label
} from 'reactstrap';
import Dropzone from 'react-dropzone';
import './SearchPage.css';

export default class SearchPage extends Component {
    constructor() {
        super();
        this.onDrop = (files) => {
            this.setState({file: files[0]})
        };
        
        this.state = {
            file: null
        };
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
                                <Input id="inputSearchTerms" placeholder="Keywords" />
                                <hr className="my-4" />
                                <Button size="lg" color="dark" rounded outline block>Search</Button>
                            </CardBody>
                        </Card>
                    </Col>
                </Row>
            </Container>
        )
    }
}
