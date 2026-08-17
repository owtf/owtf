import React from "react";
import { shallow } from "enzyme";
import "../../setupTests";
import { PluginMarketplace } from "./index";

const basePlugin = {
  id: 1,
  name: "test_plugin",
  description: "test",
  group: "web",
  type: "passive",
  author: "alice",
  rating: 0,
  approval_status: "approved",
  tags: [],
  version: "1.0.0",
  category: null,
};

const baseProps: any = {
  plugins: [basePlugin],
  loading: false,
  error: null,
  filter: {},
  uploadLoading: false,
  uploadError: null,
  uploadSuccess: null,
  runLoading: false,
  runError: null,
  runResult: null,
  onLoad: jest.fn(),
  onUpload: jest.fn(),
  onRun: jest.fn(),
  onClearUpload: jest.fn(),
  onClearRun: jest.fn(),
  onSetFilter: jest.fn(),
};

beforeEach(() => {
  (global as any).fetch = jest.fn(() =>
    Promise.resolve({ ok: false, json: () => Promise.resolve({}) })
  );
  (global as any).localStorage = {
    getItem: () => "",
    setItem: () => {},
    removeItem: () => {},
  };
});

describe("PluginMarketplace", () => {
  it("shows Browse, Upload and My Plugins tabs to a non-admin", () => {
    const wrapper = shallow(<PluginMarketplace {...baseProps} />);
    const tabButtons = wrapper.find(".marketplacePage__tabs button");
    const labels = tabButtons.map((b) => b.props().children);
    expect(labels).toContain("Browse");
    expect(labels).toContain("Upload");
    expect(labels).toContain("My Plugins");
    expect(labels).not.toContain("Pending Review");
  });

  it("shows Pending Review to an admin", () => {
    const wrapper = shallow(<PluginMarketplace {...baseProps} />);
    wrapper.setState({ isAdmin: true });
    const labels = wrapper
      .find(".marketplacePage__tabs button")
      .map((b) => b.props().children);
    expect(labels).toContain("Pending Review");
  });

  it("hides the Run on Target button from non-admin browsers", () => {
    const wrapper = shallow(<PluginMarketplace {...baseProps} />);
    const card = wrapper.instance().renderPluginCard(basePlugin, "browse");
    const cardWrapper = shallow(<div>{card}</div>);
    expect(cardWrapper.find("button").filterWhere((b) => b.text() === "Run on Target").length).toBe(0);
  });

  it("shows the Run on Target button to admin browsers", () => {
    const wrapper = shallow(<PluginMarketplace {...baseProps} />);
    wrapper.setState({ isAdmin: true });
    const card = wrapper.instance().renderPluginCard(basePlugin, "browse");
    const cardWrapper = shallow(<div>{card}</div>);
    expect(cardWrapper.find("button").filterWhere((b) => b.text() === "Run on Target").length).toBe(1);
  });

  it("renders View Source, Approve, and Reject on pending cards", () => {
    const wrapper = shallow(<PluginMarketplace {...baseProps} />);
    wrapper.setState({ isAdmin: true });
    const pending = { ...basePlugin, approval_status: "pending" };
    const card = wrapper.instance().renderPluginCard(pending, "pending");
    const cardWrapper = shallow(<div>{card}</div>);
    const labels = cardWrapper.find("button").map((b) => b.text());
    expect(labels).toContain("View Source");
    expect(labels).toContain("Approve");
    expect(labels).toContain("Reject");
  });

  it("shows rejection reason on the uploader's own rejected plugin", () => {
    const wrapper = shallow(<PluginMarketplace {...baseProps} />);
    const rejected = {
      ...basePlugin,
      approval_status: "rejected",
      rejection_reason: "uses shell=True",
    };
    const card = wrapper.instance().renderPluginCard(rejected, "mine");
    const cardWrapper = shallow(<div>{card}</div>);
    expect(cardWrapper.find(".pluginCard__rejectionReason").length).toBe(1);
    expect(cardWrapper.find(".pluginCard__rejectionReason").text()).toContain("uses shell=True");
  });

  it("opening the reject modal sets rejectModalPlugin state", () => {
    const wrapper = shallow(<PluginMarketplace {...baseProps} />);
    const pending = { ...basePlugin, approval_status: "pending" };
    wrapper.instance().openRejectModal(pending);
    expect(wrapper.state("rejectModalPlugin")).toEqual(pending);
    expect(wrapper.state("rejectReason")).toBe("");
  });

  it("switching to My Plugins triggers loadMinePlugins", () => {
    const wrapper = shallow(<PluginMarketplace {...baseProps} />);
    const spy = jest.spyOn(wrapper.instance() as any, "loadMinePlugins").mockImplementation(() => {});
    wrapper.instance().handleTabChange("mine");
    expect(spy).toHaveBeenCalled();
  });

  it("switching to Pending Review triggers loadPendingPlugins", () => {
    const wrapper = shallow(<PluginMarketplace {...baseProps} />);
    const spy = jest.spyOn(wrapper.instance() as any, "loadPendingPlugins").mockImplementation(() => {});
    wrapper.instance().handleTabChange("pending");
    expect(spy).toHaveBeenCalled();
  });
});
