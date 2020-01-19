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
            this.setState({files})
        };
        
        this.state = {
            files: []
        };
    }

    render() {
        const files = this.state.files.map(file => (
            <li key={file.name}>
                {file.name} - {file.size} bytes
            </li>
        ));
      
        return (
            <Container>
                <Row>
                    <Col sm="9" md="9" lg="9" className="mx-auto">
                        <h1 className="text-center display-1 my-5 title-text">Syft</h1>
                        <Card className="my-5">
                            <CardBody>
                                <Dropzone onDrop={this.onDrop}>
                                    {({getRootProps, getInputProps}) => (
                                    <div {...getRootProps({className: 'dropzone my-4'})}>
                                        <input {...getInputProps()} />
                                        <p>Drag 'n' drop a file, or click to get started</p>
                                    </div>
                                )}
                                </Dropzone>
                                <Input id="inputSearchTerms" placeholder="Search" />
                                <hr className="my-4" />
                                <Button size="lg" color="primary" className="text-uppercase" block>Search</Button>
                            </CardBody>
                        </Card>
                    </Col>
                </Row>
            </Container>
        )
    }
}
