import React from 'react';

class RankButtons extends React.Component {

    render() {
        var obj = this.props.obj;
        var user_rank = obj['user_rank'];
        var owtf_rank = obj['owtf_rank'];
        if (user_rank in[0,
            1,
            2,
            3,
            4,
            5]) {
            return (
                <div>
                    <label className={user_rank === 0
                        ? "btn rank"
                        : "btn rank active"} title="Passing" data-code={obj['plugin_code']}>
                        <input type="radio" name="user_rank_button"/>
                        <i className="fa fa-thumbs-up"></i>
                    </label>
                    <label className={user_rank === 1
                        ? "btn rank"
                        : "btn rank active btn-success"} title="Informational" data-code={obj['plugin_code']}>
                        <input type="radio" name="user_rank_button"/>
                        <i className="fa fa-info-circle"></i>
                    </label>
                    <label className={user_rank === 2
                        ? "btn rank"
                        : "btn rank active btn-info"} title="Low" data-code={obj['plugin_code']}>
                        <input type="radio" name="user_rank_button"/>
                        <i className="fa fa-exclamation-circle"></i>
                    </label>
                    <label className={user_rank === 3
                        ? "btn rank"
                        : "btn rank active btn-warning"} title="Medium" data-code={obj['plugin_code']}>
                        <input type="radio" name="user_rank_button"/>
                        <i className="fa fa-warning"></i>
                    </label>
                    <label className={user_rank === 4
                        ? "btn rank"
                        : "btn rank active btn-danger"} title="High" data-code={obj['plugin_code']}>
                        <input type="radio" name="user_rank_button"/>
                        <i className="fa fa-bell"></i>
                    </label>
                    <label className={user_rank === 5
                        ? "btn rank"
                        : "btn rank active btn-critical"} title="Critical" data-code={obj['plugin_code']}>
                        <input type="radio" name="user_rank_button"/>
                        <i className="fa fa-bomb"></i>
                    </label>
                </div>
            );
        } else {
            return (
                <div>
                    <label className={user_rank === 0
                        ? "btn rank"
                        : "btn rank active"} title="Passing" data-code={obj['plugin_code']}>
                        <input type="radio" name="user_rank_button"/>
                        <i className="fa fa-thumbs-up"></i>
                    </label>
                    <label className={owtf_rank === 1
                        ? "btn rank"
                        : "btn rank active btn-success"} title="Informational" data-code={obj['plugin_code']}>
                        <input type="radio" name="user_rank_button"/>
                        <i className="fa fa-info-circle"></i>
                    </label>
                    <label className={owtf_rank === 2
                        ? "btn rank"
                        : "btn rank active btn-info"} title="Low" data-code={obj['plugin_code']}>
                        <input type="radio" name="user_rank_button"/>
                        <i className="fa fa-exclamation-circle"></i>
                    </label>
                    <label className={owtf_rank === 3
                        ? "btn rank"
                        : "btn rank active btn-warning"} title="Medium" data-code={obj['plugin_code']}>
                        <input type="radio" name="user_rank_button"/>
                        <i className="fa fa-warning"></i>
                    </label>
                    <label className={owtf_rank === 4
                        ? "btn rank"
                        : "btn rank active btn-danger"} title="High" data-code={obj['plugin_code']}>
                        <input type="radio" name="user_rank_button"/>
                        <i className="fa fa-bell"></i>
                    </label>
                    <label className={user_rank === 5
                        ? "btn rank"
                        : "btn rank active btn-critical"} title="Critical" data-code={obj['plugin_code']}>
                        <input type="radio" name="user_rank_button"/>
                        <i className="fa fa-bomb"></i>
                    </label>
                </div>
            );
        }
    }
}

export default RankButtons;
