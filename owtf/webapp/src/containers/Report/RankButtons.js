
/**
  * React Component for RankButtons. It is child component used by Collapse Component.
  */

import React from 'react';
import { ButtonGroup, Button, Glyphicon } from 'react-bootstrap';

export default class RankButtons extends React.Component {

	render() {
		const { obj, patchUserRank } = this.props;
		const user_rank = obj['user_rank'];
		const owtf_rank = obj['owtf_rank'];
		const group = obj['plugin_group'];
		const type = obj['plugin_type'];
		const code = obj['plugin_code'];
		if (user_rank in [0, 1, 2, 3, 4, 5]) {
			return (
				<ButtonGroup>
					<Button bsStyle={owtf_rank === 0 ? "success" : "default"} active={user_rank === 0 ? true : false} onClick={() => patchUserRank(group, type, code, 0)}>
						<Glyphicon glyph="thumbs-up" />
					</Button>
					<Button bsStyle={user_rank === 1 ? "success" : "default"} active={user_rank === 1 ? true : false} onClick={() => patchUserRank(group, type, code, 1)}>
						<Glyphicon glyph="info-sign" />
					</Button>
					<Button bsStyle={user_rank === 2 ? "info" : "default"} active={user_rank === 2 ? true : false} onClick={() => patchUserRank(group, type, code, 2)}>
						<Glyphicon glyph="exclamation-sign" />
					</Button>
					<Button bsStyle={user_rank === 3 ? "warning" : "default"} active={user_rank === 3 ? true : false} onClick={() => patchUserRank(group, type, code, 3)}>
						<Glyphicon glyph="thumbs-up" />
					</Button>
					<Button bsStyle={user_rank === 4 ? "danger" : "default"} active={user_rank === 4 ? true : false} onClick={() => patchUserRank(group, type, code, 4)}>
						<Glyphicon glyph="bell" />
					</Button>
					<Button bsStyle={user_rank === 5 ? "danger" : "default"} active={user_rank === 5 ? true : false} onClick={() => patchUserRank(group, type, code, 5)}>
						<Glyphicon glyph="warning-sign" />
					</Button>
				</ButtonGroup>
			);
		} else {
			return (
				<ButtonGroup>
					<Button bsStyle={owtf_rank === 0 ? "success" : "default"} active={user_rank === 0 ? true : false} onClick={() => patchUserRank(group, type, code, 0)}>
						<Glyphicon glyph="thumbs-up" />
					</Button>
					<Button bsStyle={owtf_rank === 1 ? "success" : "default"} active={owtf_rank === 1 ? true : false} onClick={() => patchUserRank(group, type, code, 1)}>
						<Glyphicon glyph="info-sign" />
					</Button>
					<Button bsStyle={owtf_rank === 2 ? "info" : "default"} active={owtf_rank === 2 ? true : false} onClick={() => patchUserRank(group, type, code, 2)}>
						<Glyphicon glyph="exclamation-sign" />
					</Button>
					<Button bsStyle={owtf_rank === 3 ? "warning" : "default"} active={owtf_rank === 3 ? true : false} onClick={() => patchUserRank(group, type, code, 3)}>
						<Glyphicon glyph="thumbs-up" />
					</Button>
					<Button bsStyle={owtf_rank === 4 ? "danger" : "default"} active={owtf_rank === 4 ? true : false} onClick={() => patchUserRank(group, type, code, 4)}>
						<Glyphicon glyph="bell" />
					</Button>
					<Button bsStyle={user_rank === 5 ? "danger" : "default"} active={user_rank === 5 ? true : false} onClick={() => patchUserRank(group, type, code, 5)}>
						<Glyphicon glyph="warning-sign" />
					</Button>
				</ButtonGroup>
			);
		}
	}
}