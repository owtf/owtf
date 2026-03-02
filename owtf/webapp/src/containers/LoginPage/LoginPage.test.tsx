import React from "react";
import { shallow } from "enzyme";
import toJson from "enzyme-to-json";
import "../../setupTests";
import { findByTestAtrr, checkProps } from "../../utils/testUtils";
import { LoginPage } from "./index";
import { fromJS } from "immutable";

import { loginFail, loginSuccess } from "./actions";
import { LOGIN_START, LOGIN_SUCCESS, LOGIN_FAIL, LOGOUT } from "./constants";

import { postDataToLoginAPI } from "./saga";

import { runSaga } from "redux-saga";
import * as api from "./api";

import { loginReducer } from "./reducer";

describe("LoginPage component", () => {
  describe("Testing dumb login component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        onLogin: jest.fn()
      };
      wrapper = shallow(<LoginPage {...props} />);
    });
    it("Should have correct prop-types", () => {
      const expectedProps = {
        onLogin: () => {}
      };
      const propsErr = checkProps(LoginPage, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      const component = findByTestAtrr(wrapper, "loginPageComponent");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
    });

    it("Should correctly render its sub-components", () => {
      wrapper.setState({
        emailOrUsername: "test_user@test.com",
        password: "Test@1234",
        hidePassword: true
      });

      const heading = wrapper.find("h2");
      const textInputField = wrapper.find("input");
      const div = wrapper.find("div");
      const button = wrapper.find("button");
      expect(heading.length).toBe(1);
      expect(heading.at(0).props().children).toEqual(
        "Login with an OWTF Account"
      );
      expect(textInputField.length).toBe(2);
      expect(textInputField.at(0).props().placeholder).toEqual(
        "Username / Email"
      );
      expect(textInputField.at(1).props().placeholder).toEqual("Password");
      expect(div.length).toBe(7);
      expect(button.length).toBe(1);
      expect(button.at(0).props().children).toEqual("LOGIN");
    });

    it("Should update state on TextInputField change event", () => {
      const textInputFieldEmail = wrapper.find("input").at(0);
      const eventEmail = {
        preventDefault() {},
        target: { value: "test_user@test.com", name: "text-input-email" }
      };

      textInputFieldEmail.simulate("change", eventEmail);
      expect(wrapper.instance().state.emailOrUsername).toEqual(
        "test_user@test.com"
      );

      const textInputFieldPassword = wrapper.find("input").at(1);
      const eventPassword = {
        preventDefault() {},
        target: { value: "Test@12345", name: "text-input-password" }
      };

      textInputFieldPassword.simulate("change", eventPassword);
      expect(wrapper.instance().state.password).toEqual("Test@12345");
    });

    it("Should call onLogin on login button click", () => {
      expect(props.onLogin.mock.calls.length).toBe(0);
      const loginButton = wrapper.find("button");
      loginButton.simulate("click");
      expect(props.onLogin.mock.calls.length).toBe(1);
    });
  });

  describe("Testing the sagas", () => {
    describe("Testing postDataToLoginAPI saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
          type: LOGIN_START,
          emailOrUsername: "test_user@test.com",
          password: "Test@1234"
        };
      });

      it("Should login an user in case of success", async () => {
        const successData = {
          status: "success",
          data: {
            status: "success",
            message: {
              "jwt-token": ""
            }
          }
        };
        const dispatchedActions = [];
        api.loginUsingLoginAPI = jest.fn(() =>
          jest.fn(() => Promise.resolve(successData))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, postDataToLoginAPI, fakeAction).done;
        expect(api.loginUsingLoginAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          loginSuccess(successData["data"]["message"]["jwt-token"], "Username")
        );
      });

      it("Should handle login error in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.loginUsingLoginAPI = jest.fn(() =>
          jest.fn(() => Promise.reject(error))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, postDataToLoginAPI, fakeAction).done;
        expect(api.loginUsingLoginAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(loginFail(error));
      });
    });
    describe("Testing autoCheckLogin saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
          type: LOGIN_START,
          email: "test_user@test.com",
          password: "Test@1234"
        };
      });

      it("Should autologin an user in case of success", async () => {
        const successData = {
          status: "success",
          data: {
            status: "success",
            message: {
              "jwt-token": ""
            }
          }
        };
        const dispatchedActions = [];
        api.loginUsingLoginAPI = jest.fn(() =>
          jest.fn(() => Promise.resolve(successData))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, postDataToLoginAPI, fakeAction).done;
        expect(api.loginUsingLoginAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          loginSuccess(successData["data"]["message"]["jwt-token"], "Username")
        );
      });

      it("Should handle logout error in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.loginUsingLoginAPI = jest.fn(() =>
          jest.fn(() => Promise.reject(error))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, postDataToLoginAPI, fakeAction).done;
        expect(api.loginUsingLoginAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(loginFail(error));
      });
    });
  });

  describe("Testing reducers", () => {
    describe("Testing loginReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          token: null,
          error: false,
          loading: false,
          isAuthenticated: false,
          username: null
        };
      });

      it("Should return the initial state", () => {
        const newState = loginReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle LOGIN_START", () => {
        const newState = loginReducer(undefined, {
          type: LOGIN_START
        });
        expect(newState.toJS()).toEqual({
          loading: true,
          error: false,
          token: null,
          isAuthenticated: false,
          username: null
        });
      });

      it("Should handle LOGIN_SUCCESS", () => {
        const token = "test_token";
        const user_name = "test_user_name";
        const newState = loginReducer(
          fromJS({
            loading: true,
            error: true,
            token: null,
            isAuthenticated: false,
            username: user_name
          }),
          {
            type: LOGIN_SUCCESS,
            token: token,
            username: user_name
          }
        );

        expect(newState.toJS()).toEqual({
          loading: false,
          error: false,
          token: token,
          isAuthenticated: true,
          username: user_name
        });
      });

      it("Should handle LOGIN_FAIL", () => {
        const err = "Test sessions loading error";
        const newState = loginReducer(
          fromJS({
            loading: true,
            error: true,
            token: null,
            isAuthenticated: false,
            username: null
          }),
          {
            type: LOGIN_FAIL,
            error: err
          }
        );

        expect(newState.toJS()).toEqual({
          loading: false,
          error: err,
          token: null,
          isAuthenticated: false,
          username: null
        });
      });
    });
  });
});
