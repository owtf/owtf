// import Enzyme from 'enzyme';
// import EnzymeAdapter from 'enzyme-adapter-react-16';

// Enzyme.configure({
//     adapter: new EnzymeAdapter(),
//     disableLifecycleMethods: true
// });

import { configure } from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';

configure({ adapter: new Adapter() });
