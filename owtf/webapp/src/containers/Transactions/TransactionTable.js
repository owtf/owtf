import React from 'react';
import UnderconstructionPage from "components/UnderconstructionPage";

export default class TransactionTable extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            resizeTableActive: false,
            tableHeight: 0
        };

        // this.handleMouseMove = this.handleMouseMove.bind(this);
        // this.handleClick = this.handleClick.bind(this);
        // this.handleRowSelection = this.handleRowSelection.bind(this);
    };

    // componentDidMount() {
    //     document.addEventListener('mousemove', this.handleMouseMove);
    //     var tableBody = document.getElementsByTagName("tbody")[0];
    //     this.setState({
    //         tableHeight: (window.innerHeight - this.context.getElementTopPosition(tableBody)) / 2
    //     });
    // };

    // componentWillUnmount() {
    //     document.removeEventListener('mousemove', this.handleMouseMove);
    // };

    // handleMouseDown(e) {
    //     this.setState({resizeTableActive: true});
    // };

    // handleMouseUp(e) {
    //     this.setState({resizeTableActive: false});
    // };

    // handleMouseMove(e) {
    //     if (!this.state.resizeTableActive) {
    //         return;
    //     }

    //     var tableBody = document.getElementsByTagName("tbody")[0];
    //     this.setState({
    //         tableHeight: e.clientY - this.context.getElementTopPosition(tableBody)
    //     });

    //     this.context.handleHeaderContainerHeight(window.innerHeight - e.clientY);
    // };

    render() {
        return (
            <div></div>
        );
    }
}